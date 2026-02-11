"""
Neo-rs vector runner with connection pooling.
Uses requests.Session to avoid the ~30 connection deadlock in neo-rs.
"""
import json
import sys
import base64
import time
import gzip
from pathlib import Path
from datetime import datetime

import subprocess

RPC_URL = "http://127.0.0.1:40332"
GAS_TOLERANCE = 100000  # ignore gas diffs (ExecFeeFactor=30 at genesis)
DELAY_BETWEEN = 0.3  # seconds between RPC calls


def invoke_script(session, script_hex: str) -> dict:
    """Send invokescript RPC via subprocess curl (clean TCP per call)."""
    if script_hex.startswith("0x"):
        script_hex = script_hex[2:]
    script_bytes = bytes.fromhex(script_hex)
    b64 = base64.b64encode(script_bytes).decode("ascii")

    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "invokescript",
        "params": [b64],
    })
    result = subprocess.run(
        ["curl", "-s", "--max-time", "15", "--compressed",
         "-X", "POST", RPC_URL,
         "-H", "Content-Type: application/json",
         "-H", "Connection: close",
         "-d", payload],
        capture_output=True, timeout=20,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: rc={result.returncode}")
    raw = result.stdout
    if not raw:
        raise RuntimeError("empty response from neo-rs")
    return json.loads(raw)


def parse_stack_value(item: dict):
    """Parse a neo RPC stack item to a comparable Python value."""
    t = item.get("type", "")
    v = item.get("value")
    if t == "Integer":
        return int(v) if v is not None else 0
    if t == "Boolean":
        return bool(v) if isinstance(v, bool) else v == "true"
    if t == "ByteString":
        if v is None:
            return b""
        try:
            return base64.b64decode(v)
        except Exception:
            return v
    if t == "Buffer":
        if v is None:
            return b""
        try:
            return base64.b64decode(v)
        except Exception:
            return v
    if t in ("Array", "Struct"):
        return [parse_stack_value(x) for x in (v or [])]
    if t == "Map":
        return {str(parse_stack_value(kv["key"])): parse_stack_value(kv["value"]) for kv in (v or [])}
    if t == "Pointer":
        return int(v) if v is not None else 0
    if t == "InteropInterface":
        return "<interop>"
    return v


def normalize_expected(val):
    """Normalize expected stack value — handle both plain values and typed dicts."""
    if isinstance(val, dict) and "type" in val:
        t = val["type"]
        v = val.get("value")
        if t == "Integer":
            return int(v) if v is not None else 0
        if t == "Boolean":
            return bool(v) if isinstance(v, bool) else v == "true"
        if t == "ByteString" or t == "Buffer":
            if v is None:
                return b""
            if isinstance(v, str):
                try:
                    return bytes.fromhex(v)
                except ValueError:
                    return v.encode()
            return v
        if t in ("Array", "Struct"):
            return [normalize_expected(x) for x in (v or [])]
        if t == "Map":
            if isinstance(v, dict):
                return {str(k): normalize_expected(vv) for k, vv in v.items()}
            if isinstance(v, list):
                return {str(normalize_expected(kv["key"])): normalize_expected(kv["value"]) for kv in v}
            return v
        return v
    return val


def compare_vector(vector: dict, rpc_result: dict) -> dict:
    """Compare a single vector's expected output against RPC result."""
    result = {"vector": vector["name"], "match": True, "differences": []}

    rpc_res = rpc_result.get("result", {})
    state = rpc_res.get("state", "UNKNOWN")
    expected_error = vector.get("error")

    # State check
    if expected_error:
        if state != "FAULT":
            result["match"] = False
            result["differences"].append({
                "type": "state_mismatch",
                "path": "state",
                "python": "FAULT",
                "csharp": state,
                "message": f"State mismatch: expected FAULT, got {state}",
            })
            return result
        # FAULT expected and got FAULT — pass
        return result
    else:
        if state != "HALT":
            result["match"] = False
            result["differences"].append({
                "type": "state_mismatch",
                "path": "state",
                "python": "HALT",
                "csharp": state,
                "message": f"State mismatch: expected HALT, got {state}",
            })
            return result

    # Stack check — normalize expected values (may be plain ints or typed dicts)
    raw_expected = vector.get("post", {}).get("stack", [])
    expected_stack = [normalize_expected(v) for v in raw_expected]
    actual_stack_raw = rpc_res.get("stack", [])
    actual_stack = [parse_stack_value(item) for item in actual_stack_raw]

    if len(expected_stack) != len(actual_stack):
        result["match"] = False
        result["differences"].append({
            "type": "stack_length_mismatch",
            "path": "stack",
            "python": len(expected_stack),
            "csharp": len(actual_stack),
            "message": f"Stack length: expected {len(expected_stack)}, got {len(actual_stack)}",
        })
        return result

    for i, (exp, act) in enumerate(zip(expected_stack, actual_stack)):
        if exp != act:
            result["match"] = False
            result["differences"].append({
                "type": "stack_value_mismatch",
                "path": f"stack[{i}]",
                "python": str(exp),
                "csharp": str(act),
                "message": f"Stack[{i}]: expected {exp}, got {act}",
            })

    return result


def run_vectors(vector_file: Path, output_file: Path):
    """Run all vectors in a file against neo-rs."""
    data = json.loads(vector_file.read_text())
    vectors = data.get("vectors", [])
    if not vectors:
        print(f"  No vectors in {vector_file.name}")
        return

    results = []
    passed = 0
    failed = 0
    errors = 0

    for idx, v in enumerate(vectors):
        name = v["name"]
        script = v.get("script", "")
        if not script:
            print(f"  SKIP {name}: no script")
            continue

        if idx > 0:
            time.sleep(DELAY_BETWEEN)

        try:
            rpc_result = invoke_script(None, script)
            if "error" in rpc_result and "result" not in rpc_result:
                # RPC-level error (not VM fault)
                results.append({
                    "vector": name,
                    "match": False,
                    "differences": [{
                        "type": "rpc_error",
                        "message": str(rpc_result["error"]),
                    }],
                })
                errors += 1
                print(f"  ERROR {name}: {rpc_result['error']}")
                continue

            cmp = compare_vector(v, rpc_result)
            results.append(cmp)
            if cmp["match"]:
                passed += 1
            else:
                failed += 1
                non_gas = [d for d in cmp["differences"] if d["type"] != "gas_mismatch"]
                if non_gas:
                    print(f"  FAIL {name}: {non_gas[0]['message']}")
                else:
                    print(f"  WARN {name}: gas mismatch only")
                    passed += 1
                    failed -= 1
                    cmp["match"] = True  # treat gas-only as pass
        except Exception as e:
            results.append({
                "vector": name,
                "match": False,
                "differences": [{"type": "exception", "message": str(e)}],
            })
            errors += 1
            print(f"  ERROR {name}: {e}")

    total = passed + failed + errors
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{100*passed/total:.2f}%" if total else "N/A",
        },
        "results": results,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2))
    print(f"\n  => {passed}/{total} PASS ({report['summary']['pass_rate']})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python neo_rs_vector_runner.py <vector_file.json> [output.json]")
        sys.exit(1)

    vf = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"reports/neo-rs-batch/{vf.stem}.json")
    print(f"=== {vf.stem} ({vf}) ===")
    run_vectors(vf, out)
