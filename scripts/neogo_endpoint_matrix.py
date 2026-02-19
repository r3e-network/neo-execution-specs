"""Run a targeted NeoGo endpoint matrix check against expected C#/NeoGo deltas."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_MAINNET_CSHARP_RPC = "http://seed1.neo.org:10332"
DEFAULT_TESTNET_CSHARP_RPC = "http://seed1t5.neo.org:20332"
DEFAULT_MAINNET_NETWORK = 860833102
DEFAULT_TESTNET_NETWORK = 894710606
DEFAULT_CSHARP_USERAGENT_TOKEN = "Neo:3.9.1"
# Match NeoGo endpoints regardless of minor/patch release.
DEFAULT_NEOGO_USERAGENT_TOKEN = "NEO-GO:"
DEFAULT_MAINNET_NEOGO_RPCS = [
    "http://rpc1.n3.nspcc.ru:10332",
    "http://rpc2.n3.nspcc.ru:10332",
    "http://rpc3.n3.nspcc.ru:10332",
    "http://rpc4.n3.nspcc.ru:10332",
    "http://rpc5.n3.nspcc.ru:10332",
    "http://rpc6.n3.nspcc.ru:10332",
    "http://rpc7.n3.nspcc.ru:10332",
]
DEFAULT_TESTNET_NEOGO_RPCS = ["http://rpc.t5.n3.nspcc.ru:20332"]
DEFAULT_VECTORS_ROOT = Path("tests/vectors")
DEFAULT_EXPECTED_VECTORS_FILE = Path("docs/verification/neogo-0.116-known-deltas.txt")
DEFAULT_OUTPUT_DIR = Path("reports/compat-endpoint-matrix")
DEFAULT_PREFIX = "neogo-endpoint-matrix"
SKIP_VECTOR_FILES = {"checklist_coverage.json"}


REPO_SRC = Path(__file__).resolve().parent.parent / "src"


@dataclass
class EndpointMatrixResult:
    """Compatibility result for one NeoGo endpoint probe."""

    network: str
    csharp_rpc: str
    neogo_rpc: str
    csharp_network: int | None
    csharp_useragent: str | None
    neogo_network: int | None
    neogo_useragent: str | None
    csharp_summary: dict[str, int]
    neogo_summary: dict[str, int]
    vector_deltas: list[str]
    matches_expected: bool
    protocol_matches_expected: bool
    protocol_mismatches: list[str]
    error: str | None = None


def _run_neo_diff(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
    if str(REPO_SRC) not in sys.path:
        sys.path.insert(0, str(REPO_SRC))
    from neo.tools.diff.compat import run_neo_diff

    return run_neo_diff(vectors, rpc_url, output_path, gas_tolerance)


def _compare_report_results(
    csharp_report: dict[str, Any],
    neogo_report: dict[str, Any],
) -> list[str]:
    if str(REPO_SRC) not in sys.path:
        sys.path.insert(0, str(REPO_SRC))
    from neo.tools.diff.compat import compare_report_results

    return compare_report_results(csharp_report, neogo_report)


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser for NeoGo endpoint matrix checks."""
    parser = argparse.ArgumentParser(
        prog="neogo-endpoint-matrix",
        description=(
            "Run neo-compat-style checks across multiple NeoGo endpoints using "
            "a targeted probe vector set built from expected delta vector names."
        ),
    )
    parser.add_argument(
        "--vectors-root",
        type=Path,
        default=DEFAULT_VECTORS_ROOT,
        help=f"Vector root directory (default: {DEFAULT_VECTORS_ROOT}).",
    )
    parser.add_argument(
        "--expected-vectors-file",
        type=Path,
        default=DEFAULT_EXPECTED_VECTORS_FILE,
        help=(
            "Newline-delimited expected delta vector names ('#' comments allowed). "
            f"Default: {DEFAULT_EXPECTED_VECTORS_FILE}."
        ),
    )
    parser.add_argument(
        "--mainnet-csharp-rpc",
        type=str,
        default=DEFAULT_MAINNET_CSHARP_RPC,
        help=f"MainNet C# RPC endpoint (default: {DEFAULT_MAINNET_CSHARP_RPC}).",
    )
    parser.add_argument(
        "--testnet-csharp-rpc",
        type=str,
        default=DEFAULT_TESTNET_CSHARP_RPC,
        help=f"TestNet C# RPC endpoint (default: {DEFAULT_TESTNET_CSHARP_RPC}).",
    )
    parser.add_argument(
        "--expected-mainnet-network",
        type=int,
        default=DEFAULT_MAINNET_NETWORK,
        help=f"Expected MainNet network magic (default: {DEFAULT_MAINNET_NETWORK}).",
    )
    parser.add_argument(
        "--expected-testnet-network",
        type=int,
        default=DEFAULT_TESTNET_NETWORK,
        help=f"Expected TestNet network magic (default: {DEFAULT_TESTNET_NETWORK}).",
    )
    parser.add_argument(
        "--csharp-useragent-token",
        type=str,
        default=DEFAULT_CSHARP_USERAGENT_TOKEN,
        help=(
            "Substring required in C# endpoint useragent "
            f"(default: {DEFAULT_CSHARP_USERAGENT_TOKEN})."
        ),
    )
    parser.add_argument(
        "--neogo-useragent-token",
        type=str,
        default=DEFAULT_NEOGO_USERAGENT_TOKEN,
        help=(
            "Substring required in NeoGo endpoint useragent "
            f"(default: {DEFAULT_NEOGO_USERAGENT_TOKEN})."
        ),
    )
    parser.add_argument(
        "--mainnet-neogo-rpcs",
        type=str,
        default=",".join(DEFAULT_MAINNET_NEOGO_RPCS),
        help="Comma-delimited MainNet NeoGo RPC endpoints.",
    )
    parser.add_argument(
        "--testnet-neogo-rpcs",
        type=str,
        default=",".join(DEFAULT_TESTNET_NEOGO_RPCS),
        help="Comma-delimited TestNet NeoGo RPC endpoints.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for reports and summary (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=DEFAULT_PREFIX,
        help=f"Output filename prefix (default: {DEFAULT_PREFIX}).",
    )
    parser.add_argument(
        "--gas-tolerance",
        type=int,
        default=0,
        help="Pass-through gas tolerance for neo-diff (default: 0).",
    )
    parser.add_argument(
        "--rpc-timeout-seconds",
        type=float,
        default=5.0,
        help="RPC timeout for getversion probes (default: 5.0).",
    )
    parser.add_argument(
        "--keep-probe-vectors",
        action="store_true",
        help="Keep generated probe vectors under output directory.",
    )
    parser.add_argument(
        "--allow-inconsistent",
        action="store_true",
        help="Return success even when endpoint results do not match expected vectors.",
    )
    parser.add_argument(
        "--disable-protocol-checks",
        action="store_true",
        help="Disable expected network/useragent protocol checks.",
    )
    return parser


def _split_csv(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid JSON object in {path}")
    return raw


def _load_expected_vectors(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Expected vectors file not found: {path}")
    expected: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            expected.append(stripped)
    if not expected:
        raise ValueError(f"Expected vectors file is empty: {path}")
    if len(expected) != len(set(expected)):
        raise ValueError(f"Expected vectors file has duplicates: {path}")
    return expected


def _build_probe_vectors(
    vectors_root: Path,
    expected_names: set[str],
    probe_root: Path,
) -> None:
    if not vectors_root.exists() or not vectors_root.is_dir():
        raise FileNotFoundError(f"Vectors root not found: {vectors_root}")

    found_sources: dict[str, Path] = {}

    for source_file in sorted(vectors_root.rglob("*.json")):
        if source_file.name in SKIP_VECTOR_FILES:
            continue
        source = _load_json(source_file)
        vectors_raw = source.get("vectors")
        if not isinstance(vectors_raw, list):
            continue

        selected_vectors: list[dict[str, Any]] = []
        for vector in vectors_raw:
            if not isinstance(vector, dict):
                continue
            vector_name = vector.get("name")
            if not isinstance(vector_name, str) or vector_name not in expected_names:
                continue
            existing_source = found_sources.get(vector_name)
            if existing_source is not None and existing_source != source_file:
                raise ValueError(
                    f"Vector {vector_name} found in multiple files: "
                    f"{existing_source} and {source_file}"
                )
            found_sources[vector_name] = source_file
            selected_vectors.append(vector)

        if not selected_vectors:
            continue

        probe_payload = dict(source)
        probe_payload["vectors"] = selected_vectors
        out_path = probe_root / source_file.relative_to(vectors_root)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as handle:
            json.dump(probe_payload, handle, indent=2)
            handle.write("\n")

    missing_vectors = expected_names - set(found_sources)
    if missing_vectors:
        missing = ", ".join(sorted(missing_vectors))
        raise ValueError(f"Expected vectors were not found under {vectors_root}: {missing}")


def _summary(report: dict[str, Any]) -> dict[str, int]:
    results = report.get("results")
    if not isinstance(results, list):
        return {"total": 0, "passed": 0, "failed": 0, "errors": 1}

    total = 0
    passed = 0
    for entry in results:
        if not isinstance(entry, dict):
            continue
        total += 1
        if bool(entry.get("match", False)):
            passed += 1

    summary_raw = report.get("summary")
    errors = 0
    if isinstance(summary_raw, dict):
        errors_value = summary_raw.get("errors", 0)
        if isinstance(errors_value, int):
            errors = errors_value
        elif isinstance(errors_value, str) and errors_value.isdigit():
            errors = int(errors_value)

    return {"total": total, "passed": passed, "failed": total - passed, "errors": errors}


def _endpoint_label(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    raw = parsed.netloc or parsed.path or endpoint
    return "".join(ch if ch.isalnum() else "-" for ch in raw).strip("-")


def _getversion(endpoint: str, timeout_seconds: float) -> tuple[int | None, str | None]:
    payload = {"jsonrpc": "2.0", "method": "getversion", "params": [], "id": 1}
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return (None, None)

    if not isinstance(response_payload, dict):
        return (None, None)
    result = response_payload.get("result")
    if not isinstance(result, dict):
        return (None, None)

    network: int | None = None
    protocol = result.get("protocol")
    if isinstance(protocol, dict):
        network_raw = protocol.get("network")
        if isinstance(network_raw, int):
            network = network_raw
        elif isinstance(network_raw, str) and network_raw.isdigit():
            network = int(network_raw)

    useragent_raw = result.get("useragent")
    useragent = useragent_raw if isinstance(useragent_raw, str) else None
    return (network, useragent)


def _protocol_mismatches(
    *,
    expected_network: int,
    csharp_network: int | None,
    neogo_network: int | None,
    csharp_useragent: str | None,
    neogo_useragent: str | None,
    csharp_useragent_token: str,
    neogo_useragent_token: str,
    enable_checks: bool,
) -> list[str]:
    mismatches: list[str] = []
    if not enable_checks:
        return mismatches

    if csharp_network != expected_network:
        mismatches.append(
            f"csharp_network_expected_{expected_network}_got_{csharp_network}"
        )
    if neogo_network != expected_network:
        mismatches.append(
            f"neogo_network_expected_{expected_network}_got_{neogo_network}"
        )

    if csharp_useragent is None or csharp_useragent_token not in csharp_useragent:
        mismatches.append(
            f"csharp_useragent_missing_token_{csharp_useragent_token}"
        )
    if neogo_useragent is None or neogo_useragent_token not in neogo_useragent:
        mismatches.append(
            f"neogo_useragent_missing_token_{neogo_useragent_token}"
        )

    return mismatches


def _run_endpoint_probe(
    network: str,
    csharp_rpc: str,
    neogo_rpc: str,
    vectors_path: Path,
    output_dir: Path,
    prefix: str,
    gas_tolerance: int,
    expected_vectors: set[str],
    expected_network: int,
    csharp_useragent_token: str,
    neogo_useragent_token: str,
    enforce_protocol_checks: bool,
    rpc_timeout_seconds: float,
) -> EndpointMatrixResult:
    endpoint_id = _endpoint_label(neogo_rpc)
    csharp_output = output_dir / f"{prefix}-{network}-{endpoint_id}-csharp.json"
    neogo_output = output_dir / f"{prefix}-{network}-{endpoint_id}-neogo.json"

    csharp_exit = _run_neo_diff(vectors_path, csharp_rpc, csharp_output, gas_tolerance)
    neogo_exit = _run_neo_diff(vectors_path, neogo_rpc, neogo_output, gas_tolerance)

    csharp_network, csharp_useragent = _getversion(csharp_rpc, rpc_timeout_seconds)
    neogo_network, neogo_useragent = _getversion(neogo_rpc, rpc_timeout_seconds)
    protocol_mismatches = _protocol_mismatches(
        expected_network=expected_network,
        csharp_network=csharp_network,
        neogo_network=neogo_network,
        csharp_useragent=csharp_useragent,
        neogo_useragent=neogo_useragent,
        csharp_useragent_token=csharp_useragent_token,
        neogo_useragent_token=neogo_useragent_token,
        enable_checks=enforce_protocol_checks,
    )
    protocol_matches_expected = len(protocol_mismatches) == 0

    if csharp_exit not in (0, 1):
        return EndpointMatrixResult(
            network=network,
            csharp_rpc=csharp_rpc,
            neogo_rpc=neogo_rpc,
            csharp_network=csharp_network,
            csharp_useragent=csharp_useragent,
            neogo_network=neogo_network,
            neogo_useragent=neogo_useragent,
            csharp_summary={"total": 0, "passed": 0, "failed": 0, "errors": 1},
            neogo_summary={"total": 0, "passed": 0, "failed": 0, "errors": 1},
            vector_deltas=[],
            matches_expected=False,
            protocol_matches_expected=protocol_matches_expected,
            protocol_mismatches=protocol_mismatches,
            error=f"C# neo-diff failed with exit code {csharp_exit}",
        )
    if neogo_exit not in (0, 1):
        return EndpointMatrixResult(
            network=network,
            csharp_rpc=csharp_rpc,
            neogo_rpc=neogo_rpc,
            csharp_network=csharp_network,
            csharp_useragent=csharp_useragent,
            neogo_network=neogo_network,
            neogo_useragent=neogo_useragent,
            csharp_summary={"total": 0, "passed": 0, "failed": 0, "errors": 1},
            neogo_summary={"total": 0, "passed": 0, "failed": 0, "errors": 1},
            vector_deltas=[],
            matches_expected=False,
            protocol_matches_expected=protocol_matches_expected,
            protocol_mismatches=protocol_mismatches,
            error=f"NeoGo neo-diff failed with exit code {neogo_exit}",
        )
    if not csharp_output.exists() or not neogo_output.exists():
        return EndpointMatrixResult(
            network=network,
            csharp_rpc=csharp_rpc,
            neogo_rpc=neogo_rpc,
            csharp_network=csharp_network,
            csharp_useragent=csharp_useragent,
            neogo_network=neogo_network,
            neogo_useragent=neogo_useragent,
            csharp_summary={"total": 0, "passed": 0, "failed": 0, "errors": 1},
            neogo_summary={"total": 0, "passed": 0, "failed": 0, "errors": 1},
            vector_deltas=[],
            matches_expected=False,
            protocol_matches_expected=protocol_matches_expected,
            protocol_mismatches=protocol_mismatches,
            error="Expected report output missing",
        )

    csharp_report = _load_json(csharp_output)
    neogo_report = _load_json(neogo_output)
    vector_deltas = _compare_report_results(csharp_report, neogo_report)
    matches_expected = set(vector_deltas) == expected_vectors

    return EndpointMatrixResult(
        network=network,
        csharp_rpc=csharp_rpc,
        neogo_rpc=neogo_rpc,
        csharp_network=csharp_network,
        csharp_useragent=csharp_useragent,
        neogo_network=neogo_network,
        neogo_useragent=neogo_useragent,
        csharp_summary=_summary(csharp_report),
        neogo_summary=_summary(neogo_report),
        vector_deltas=vector_deltas,
        matches_expected=matches_expected,
        protocol_matches_expected=protocol_matches_expected,
        protocol_mismatches=protocol_mismatches,
        error=None,
    )


def _write_summary(
    output_path: Path,
    expected_vectors: list[str],
    probe_vectors_root: Path,
    results: list[EndpointMatrixResult],
) -> None:
    all_vector_matches_expected = all(
        result.matches_expected for result in results if result.error is None
    )
    all_protocol_matches_expected = all(
        result.protocol_matches_expected for result in results if result.error is None
    )
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "expected_vectors": expected_vectors,
        "probe_vectors_root": str(probe_vectors_root),
        "results": [asdict(result) for result in results],
        "all_vector_matches_expected": all_vector_matches_expected,
        "all_protocol_matches_expected": all_protocol_matches_expected,
        "all_matches_expected": all_vector_matches_expected and all_protocol_matches_expected,
        "had_errors": any(result.error is not None for result in results),
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    """Execute the endpoint matrix probe."""
    args = create_parser().parse_args(argv)

    expected_vectors = _load_expected_vectors(args.expected_vectors_file)
    expected_vector_set = set(expected_vectors)

    mainnet_endpoints = _split_csv(args.mainnet_neogo_rpcs)
    testnet_endpoints = _split_csv(args.testnet_neogo_rpcs)
    if not mainnet_endpoints and not testnet_endpoints:
        print("No NeoGo endpoints provided.", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.keep_probe_vectors:
        probe_root = args.output_dir / f"{args.prefix}-probe-vectors"
        if probe_root.exists():
            shutil.rmtree(probe_root)
        probe_root.mkdir(parents=True, exist_ok=True)
        cleanup_probe_root = False
    else:
        probe_root = Path(tempfile.mkdtemp(prefix=f"{args.prefix}-probe-"))
        cleanup_probe_root = True

    try:
        _build_probe_vectors(args.vectors_root, expected_vector_set, probe_root)

        results: list[EndpointMatrixResult] = []
        for endpoint in mainnet_endpoints:
            print(f"[mainnet] probing {endpoint}")
            results.append(
                _run_endpoint_probe(
                    network="mainnet",
                    csharp_rpc=args.mainnet_csharp_rpc,
                    neogo_rpc=endpoint,
                    vectors_path=probe_root,
                    output_dir=args.output_dir,
                    prefix=args.prefix,
                    gas_tolerance=args.gas_tolerance,
                    expected_vectors=expected_vector_set,
                    expected_network=args.expected_mainnet_network,
                    csharp_useragent_token=args.csharp_useragent_token,
                    neogo_useragent_token=args.neogo_useragent_token,
                    enforce_protocol_checks=not args.disable_protocol_checks,
                    rpc_timeout_seconds=args.rpc_timeout_seconds,
                )
            )
        for endpoint in testnet_endpoints:
            print(f"[testnet] probing {endpoint}")
            results.append(
                _run_endpoint_probe(
                    network="testnet",
                    csharp_rpc=args.testnet_csharp_rpc,
                    neogo_rpc=endpoint,
                    vectors_path=probe_root,
                    output_dir=args.output_dir,
                    prefix=args.prefix,
                    gas_tolerance=args.gas_tolerance,
                    expected_vectors=expected_vector_set,
                    expected_network=args.expected_testnet_network,
                    csharp_useragent_token=args.csharp_useragent_token,
                    neogo_useragent_token=args.neogo_useragent_token,
                    enforce_protocol_checks=not args.disable_protocol_checks,
                    rpc_timeout_seconds=args.rpc_timeout_seconds,
                )
            )

        summary_path = args.output_dir / f"{args.prefix}-summary.json"
        _write_summary(summary_path, expected_vectors, probe_root, results)

        print("\nEndpoint Matrix Summary")
        print("=" * 60)
        for result in results:
            delta_count = len(result.vector_deltas)
            expected_count = len(expected_vectors)
            print(
                f"- {result.network} {result.neogo_rpc}: "
                f"deltas={delta_count}/{expected_count}, "
                f"match_expected={result.matches_expected}, "
                f"protocol_ok={result.protocol_matches_expected}"
            )
            if result.neogo_useragent is not None:
                print(
                    f"  useragent={result.neogo_useragent}, "
                    f"network={result.neogo_network}"
                )
            if result.protocol_mismatches:
                print("  protocol_mismatches=" + ", ".join(result.protocol_mismatches))
            if result.error is not None:
                print(f"  error={result.error}")

        print(f"\nSummary JSON: {summary_path}")

        has_errors = any(result.error is not None for result in results)
        vector_mismatched = any(
            result.error is None and not result.matches_expected for result in results
        )
        protocol_mismatched = any(
            result.error is None and not result.protocol_matches_expected for result in results
        )
        if args.allow_inconsistent:
            return 1 if has_errors else 0
        return 1 if has_errors or vector_mismatched or protocol_mismatched else 0
    finally:
        if cleanup_probe_root:
            shutil.rmtree(probe_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
