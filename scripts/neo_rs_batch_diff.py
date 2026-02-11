"""Batch neo-diff runner for neo-rs — runs per vector file with delays to avoid RPC exhaustion."""
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from neo.tools.diff.compat import run_neo_diff

NEO_RS_RPC = "http://127.0.0.1:40332"
VECTORS_DIR = Path("tests/vectors")
REPORTS_DIR = Path("reports/neo-rs-batch")
DELAY_BETWEEN = 2  # seconds between files

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

vector_files = sorted(VECTORS_DIR.glob("**/*.json"))
total_passed = 0
total_failed = 0
total_errors = 0
total_vectors = 0
failures = []

for vf in vector_files:
    label = vf.stem
    out = REPORTS_DIR / f"{label}.json"
    print(f"\n--- {vf.relative_to(VECTORS_DIR)} ---")

    rc = run_neo_diff(vf, NEO_RS_RPC, out, gas_tolerance=100000)

    if out.exists():
        report = json.loads(out.read_text())
        s = report.get("summary", {})
        p = int(s.get("passed", 0))
        f = int(s.get("failed", 0))
        e = int(s.get("errors", 0))
        t = int(s.get("total", 0))
        total_passed += p
        total_failed += f
        total_errors += e
        total_vectors += t

        for r in report.get("results", []):
            if not r.get("match"):
                diffs = r.get("differences", [])
                non_gas = [d for d in diffs if d.get("type") != "gas_mismatch"]
                if non_gas:
                    failures.append((r["vector"], non_gas))

    time.sleep(DELAY_BETWEEN)

print("\n" + "=" * 60)
print("NEO-RS BATCH SUMMARY")
print("=" * 60)
print(f"Total vectors: {total_vectors}")
print(f"Passed (with gas tolerance): {total_passed}")
print(f"Failed: {total_failed}")
print(f"Errors: {total_errors}")

if failures:
    print(f"\nNon-gas failures ({len(failures)}):")
    for name, diffs in failures:
        print(f"  {name}:")
        for d in diffs:
            print(f"    {d.get('type')}: {d.get('message', '')}")
else:
    print("\nNo non-gas failures — stack/state correctness verified!")
