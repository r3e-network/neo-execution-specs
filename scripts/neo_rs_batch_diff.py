"""Run neo-diff across all vector files against neo-rs and summarize compatibility."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_NEO_RS_RPC = "http://127.0.0.1:40332"
DEFAULT_VECTORS_DIR = Path("tests/vectors")
DEFAULT_REPORTS_DIR = Path("reports/neo-rs-batch")
DEFAULT_DELAY_SECONDS = 2.0
DEFAULT_GAS_TOLERANCE = 100_000
SKIP_JSON_FILES = {"checklist_coverage.json"}


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser for batch neo-rs compatibility runs."""
    parser = argparse.ArgumentParser(
        prog="neo-rs-batch-diff",
        description=(
            "Run neo-diff over all vector JSON files and summarize non-gas mismatches "
            "against a neo-rs RPC endpoint."
        ),
    )
    parser.add_argument(
        "--vectors-dir",
        type=Path,
        default=DEFAULT_VECTORS_DIR,
        help=f"Vector directory to scan (default: {DEFAULT_VECTORS_DIR}).",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help=f"Directory for per-file JSON reports (default: {DEFAULT_REPORTS_DIR}).",
    )
    parser.add_argument(
        "--rpc-url",
        type=str,
        default=DEFAULT_NEO_RS_RPC,
        help=f"neo-rs RPC endpoint (default: {DEFAULT_NEO_RS_RPC}).",
    )
    parser.add_argument(
        "--gas-tolerance",
        type=int,
        default=DEFAULT_GAS_TOLERANCE,
        help=f"Allowed gas mismatch tolerance (default: {DEFAULT_GAS_TOLERANCE}).",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"Delay between files in seconds (default: {DEFAULT_DELAY_SECONDS}).",
    )
    parser.add_argument(
        "--fail-on-gas-mismatch",
        action="store_true",
        help="Return non-zero when only gas mismatches remain.",
    )
    return parser


def _run_neo_diff(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
    repo_src = Path(__file__).resolve().parent.parent / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))

    from neo.tools.diff.compat import run_neo_diff

    return run_neo_diff(vectors, rpc_url, output_path, gas_tolerance)


def _load_report(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as report_file:
        payload = json.load(report_file)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid report payload in {path}")
    return payload


def _summary_value(summary: dict[str, Any], key: str) -> int:
    value = summary.get(key, 0)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _classify_differences(entry: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_differences = entry.get("differences")
    if not isinstance(raw_differences, list):
        return ([], [])

    gas_diffs: list[dict[str, Any]] = []
    non_gas_diffs: list[dict[str, Any]] = []

    for difference in raw_differences:
        if not isinstance(difference, dict):
            continue
        diff_type = str(difference.get("type", ""))
        if diff_type == "gas_mismatch":
            gas_diffs.append(difference)
        else:
            non_gas_diffs.append(difference)

    return (gas_diffs, non_gas_diffs)


def _iter_vector_reports(vectors_dir: Path) -> list[Path]:
    vector_files = sorted(path for path in vectors_dir.glob("**/*.json") if path.is_file())
    return [path for path in vector_files if path.name not in SKIP_JSON_FILES]


def main(argv: list[str] | None = None) -> int:
    """Execute batch compatibility checks and return a CI-friendly exit status."""
    args = create_parser().parse_args(argv)

    if not args.vectors_dir.exists() or not args.vectors_dir.is_dir():
        print(f"Vectors directory not found: {args.vectors_dir}", file=sys.stderr)
        return 2

    vector_files = _iter_vector_reports(args.vectors_dir)
    if not vector_files:
        print(f"No vector JSON files found under: {args.vectors_dir}", file=sys.stderr)
        return 2

    args.reports_dir.mkdir(parents=True, exist_ok=True)

    total_vectors = 0
    raw_passed = 0
    raw_failed = 0
    raw_errors = 0

    effective_passed = 0
    effective_failed = 0
    effective_errors = 0

    non_gas_failures: list[tuple[str, list[dict[str, Any]]]] = []

    for index, vector_file in enumerate(vector_files):
        if index > 0 and args.delay_seconds > 0:
            time.sleep(args.delay_seconds)

        output_path = args.reports_dir / f"{vector_file.stem}.json"
        print(f"\n--- {vector_file.relative_to(args.vectors_dir)} ---")

        exit_code = _run_neo_diff(vector_file, args.rpc_url, output_path, args.gas_tolerance)
        if exit_code not in (0, 1):
            print(f"neo-diff command failed for {vector_file} (exit={exit_code})", file=sys.stderr)
            return 1

        if not output_path.exists():
            print(f"Expected report file not created: {output_path}", file=sys.stderr)
            return 1

        report = _load_report(output_path)
        summary_raw = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        assert isinstance(summary_raw, dict)

        file_total = _summary_value(summary_raw, "total")
        file_passed = _summary_value(summary_raw, "passed")
        file_failed = _summary_value(summary_raw, "failed")
        file_errors = _summary_value(summary_raw, "errors")

        total_vectors += file_total
        raw_passed += file_passed
        raw_failed += file_failed
        raw_errors += file_errors

        file_effective_passed = 0
        file_effective_failed = 0
        file_effective_errors = 0

        results = report.get("results")
        if not isinstance(results, list):
            file_effective_errors += file_errors or 1
        else:
            for entry in results:
                if not isinstance(entry, dict):
                    file_effective_errors += 1
                    continue

                if entry.get("match", False):
                    file_effective_passed += 1
                    continue

                gas_diffs, non_gas_diffs = _classify_differences(entry)
                vector_name = str(entry.get("vector", "<unknown>"))

                if non_gas_diffs:
                    file_effective_failed += 1
                    non_gas_failures.append((vector_name, non_gas_diffs))
                elif gas_diffs:
                    if args.fail_on_gas_mismatch:
                        file_effective_failed += 1
                    else:
                        file_effective_passed += 1
                else:
                    file_effective_errors += 1

        effective_passed += file_effective_passed
        effective_failed += file_effective_failed
        effective_errors += file_effective_errors

    print("\n" + "=" * 64)
    print("NEO-RS BATCH SUMMARY")
    print("=" * 64)
    print(
        f"Raw totals: total={total_vectors}, passed={raw_passed}, "
        f"failed={raw_failed}, errors={raw_errors}"
    )
    print(
        f"Effective totals (gas-policy aware): passed={effective_passed}, "
        f"failed={effective_failed}, errors={effective_errors}"
    )

    if non_gas_failures:
        print(f"\nNon-gas failures ({len(non_gas_failures)}):")
        for vector_name, differences in non_gas_failures:
            print(f"- {vector_name}")
            for difference in differences:
                diff_type = str(difference.get("type", "unknown"))
                message = str(difference.get("message", "<no message>"))
                print(f"  - {diff_type}: {message}")
    else:
        print("\nNo non-gas failures detected.")

    if effective_errors > 0:
        return 1
    if effective_failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
