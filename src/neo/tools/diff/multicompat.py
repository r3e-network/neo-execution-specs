"""CLI utility to validate C# vs NeoGo vs neo-rs compatibility via shared vectors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from neo.tools.diff.compat import compare_report_results, run_neo_diff
import json


DEFAULT_CSHARP_RPC = "http://seed1.neo.org:10332"
DEFAULT_NEOGO_RPC = "http://rpc3.n3.nspcc.ru:10332"
DEFAULT_NEO_RS_RPC = "http://127.0.0.1:40332"
DEFAULT_OUTPUT_PREFIX = "compat-triplet"


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser for C#/NeoGo/neo-rs compatibility checks."""
    parser = argparse.ArgumentParser(
        prog="neo-multicompat",
        description="Run neo-diff across C#, NeoGo, and neo-rs RPC endpoints and compare outcomes.",
    )
    parser.add_argument(
        "--vectors",
        "-v",
        type=Path,
        default=Path("tests/vectors/"),
        help="Path to vector file or directory.",
    )
    parser.add_argument(
        "--csharp-rpc",
        type=str,
        default=DEFAULT_CSHARP_RPC,
        help=f"C# RPC endpoint (default: {DEFAULT_CSHARP_RPC}).",
    )
    parser.add_argument(
        "--neogo-rpc",
        type=str,
        default=DEFAULT_NEOGO_RPC,
        help=f"NeoGo RPC endpoint (default: {DEFAULT_NEOGO_RPC}).",
    )
    parser.add_argument(
        "--neo-rs-rpc",
        type=str,
        default=DEFAULT_NEO_RS_RPC,
        help=f"neo-rs RPC endpoint (default: {DEFAULT_NEO_RS_RPC}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory to write neo-diff JSON reports.",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=DEFAULT_OUTPUT_PREFIX,
        help=f"Filename prefix for generated reports (default: {DEFAULT_OUTPUT_PREFIX}).",
    )
    parser.add_argument(
        "--gas-tolerance",
        type=int,
        default=0,
        help="Pass-through gas tolerance for neo-diff.",
    )
    parser.add_argument(
        "--allow-shared-failures",
        action="store_true",
        help="Return success when all pairwise deltas are zero, even if vectors fail on all endpoints.",
    )
    return parser


def _load_report(path: Path) -> dict[str, Any]:
    with open(path) as report_file:
        raw_report = json.load(report_file)
    if not isinstance(raw_report, dict):
        raise ValueError(f"Invalid report structure in {path}")
    return raw_report


def _summary(report: dict[str, Any]) -> dict[str, int]:
    summary_raw = report.get("summary")
    if not isinstance(summary_raw, dict):
        return {"total": 0, "passed": 0, "failed": 0, "errors": 0}

    def _as_int(name: str) -> int:
        value = summary_raw.get(name, 0)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return 0

    return {
        "total": _as_int("total"),
        "passed": _as_int("passed"),
        "failed": _as_int("failed"),
        "errors": _as_int("errors"),
    }


def compare_triplet_reports(reports: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """Return pairwise vector deltas for three client reports."""
    labels = sorted(reports)
    deltas: dict[str, list[str]] = {}

    for index, left_label in enumerate(labels):
        for right_label in labels[index + 1 :]:
            key = f"{left_label}_vs_{right_label}"
            deltas[key] = compare_report_results(reports[left_label], reports[right_label])

    return deltas


def is_strictly_compatible_triplet(
    summaries: dict[str, dict[str, int]],
    pairwise_deltas: dict[str, list[str]],
) -> bool:
    """Strict compatibility requires zero failures/errors and zero pairwise deltas."""
    if any(pairwise_deltas.values()):
        return False

    totals = {summary.get("total", 0) for summary in summaries.values()}
    if len(totals) != 1:
        return False

    for summary in summaries.values():
        if summary.get("failed", 0) != 0 or summary.get("errors", 0) != 0:
            return False

    return True


def _run_report(
    vectors: Path,
    rpc_url: str,
    output_path: Path,
    gas_tolerance: int,
) -> int:
    return run_neo_diff(vectors, rpc_url, output_path, gas_tolerance)


def main(argv: list[str] | None = None) -> int:
    """Run compatibility checks for C#, NeoGo, and neo-rs endpoints."""
    parser = create_parser()
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    clients = {
        "csharp": args.csharp_rpc,
        "neogo": args.neogo_rpc,
        "neo_rs": args.neo_rs_rpc,
    }
    outputs = {
        label: args.output_dir / f"{args.prefix}-{label}.json"
        for label in clients
    }

    exit_codes: dict[str, int] = {}
    for label, endpoint in clients.items():
        print(f"Running {label} endpoint against: {endpoint}")
        exit_codes[label] = _run_report(
            args.vectors,
            endpoint,
            outputs[label],
            args.gas_tolerance,
        )

    if any(code not in (0, 1) for code in exit_codes.values()):
        print("neo-diff command execution failed", file=sys.stderr)
        return 1

    for path in outputs.values():
        if not path.exists():
            print(f"neo-diff report output missing: {path}", file=sys.stderr)
            return 1

    reports = {label: _load_report(path) for label, path in outputs.items()}
    summaries = {label: _summary(report) for label, report in reports.items()}
    pairwise_deltas = compare_triplet_reports(reports)

    print("\nTriplet summaries:")
    for label in sorted(summaries):
        print(f"  - {label}: {summaries[label]}")

    print("\nPairwise vector deltas:")
    for pair in sorted(pairwise_deltas):
        print(f"  - {pair}: {len(pairwise_deltas[pair])}")

    if args.allow_shared_failures:
        return 0 if all(len(deltas) == 0 for deltas in pairwise_deltas.values()) else 1

    return 0 if is_strictly_compatible_triplet(summaries, pairwise_deltas) else 1


if __name__ == "__main__":
    raise SystemExit(main())
