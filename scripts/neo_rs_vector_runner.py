"""Run one vector file against neo-rs and produce a normalized neo-diff report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _run_neo_diff(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
    repo_src = Path(__file__).resolve().parent.parent / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))

    from neo.tools.diff.compat import run_neo_diff

    return run_neo_diff(vectors, rpc_url, output_path, gas_tolerance)


DEFAULT_RPC_URL = "http://127.0.0.1:40332"
DEFAULT_GAS_TOLERANCE = 100_000


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser for single-file neo-rs vector validation."""
    parser = argparse.ArgumentParser(
        prog="neo-rs-vector-runner",
        description="Run one vector file against neo-rs and emit a neo-diff report.",
    )
    parser.add_argument("vector_file", type=Path, help="Path to vector JSON file.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output report path (default: reports/neo-rs-batch/<vector>.json).",
    )
    parser.add_argument(
        "--rpc-url",
        type=str,
        default=DEFAULT_RPC_URL,
        help=f"neo-rs RPC endpoint (default: {DEFAULT_RPC_URL}).",
    )
    parser.add_argument(
        "--gas-tolerance",
        type=int,
        default=DEFAULT_GAS_TOLERANCE,
        help=f"Allowed gas mismatch tolerance (default: {DEFAULT_GAS_TOLERANCE}).",
    )
    parser.add_argument(
        "--show-failures",
        action="store_true",
        help="Print non-gas mismatch details from the generated report.",
    )
    return parser


def _load_report(report_path: Path) -> dict[str, Any]:
    with report_path.open("r", encoding="utf-8") as report_file:
        data = json.load(report_file)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid report structure in {report_path}")
    return data


def _summary_value(summary: dict[str, Any], key: str) -> int:
    value = summary.get(key, 0)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _collect_non_gas_failures(report: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    failures: list[tuple[str, list[dict[str, Any]]]] = []
    results = report.get("results")
    if not isinstance(results, list):
        return failures

    for entry in results:
        if not isinstance(entry, dict) or entry.get("match", False):
            continue

        vector_name = str(entry.get("vector", "<unknown>"))
        raw_differences = entry.get("differences")
        if not isinstance(raw_differences, list):
            failures.append((vector_name, []))
            continue

        non_gas_differences = [
            difference
            for difference in raw_differences
            if isinstance(difference, dict)
            and str(difference.get("type", "")) != "gas_mismatch"
        ]
        if non_gas_differences:
            failures.append((vector_name, non_gas_differences))

    return failures


def main(argv: list[str] | None = None) -> int:
    """Execute one vector file against neo-rs and return CI-friendly status code."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.vector_file.exists() or not args.vector_file.is_file():
        print(f"Vector file not found: {args.vector_file}", file=sys.stderr)
        return 2

    output_path = args.output or Path(f"reports/neo-rs-batch/{args.vector_file.stem}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== {args.vector_file.stem} ({args.vector_file}) ===")
    command_status = _run_neo_diff(args.vector_file, args.rpc_url, output_path, args.gas_tolerance)
    if command_status not in (0, 1):
        print(f"neo-diff execution failed with code {command_status}", file=sys.stderr)
        return 1

    if not output_path.exists():
        print(f"Expected report output was not created: {output_path}", file=sys.stderr)
        return 1

    report = _load_report(output_path)
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    assert isinstance(summary, dict)

    total = _summary_value(summary, "total")
    passed = _summary_value(summary, "passed")
    failed = _summary_value(summary, "failed")
    errors = _summary_value(summary, "errors")

    print(f"\nSummary: total={total}, passed={passed}, failed={failed}, errors={errors}")

    non_gas_failures = _collect_non_gas_failures(report)
    if args.show_failures and non_gas_failures:
        print("\nNon-gas failures:")
        for vector_name, differences in non_gas_failures:
            print(f"- {vector_name}")
            for difference in differences:
                message = str(difference.get("message", "<no message>"))
                diff_type = str(difference.get("type", "unknown"))
                print(f"  - {diff_type}: {message}")

    return 1 if errors > 0 or non_gas_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
