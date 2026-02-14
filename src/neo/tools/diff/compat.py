"""CLI utility to validate C# vs NeoGo compatibility via shared vectors."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CSHARP_RPC = "http://seed1.neo.org:10332"
DEFAULT_NEOGO_RPC = "http://rpc3.n3.nspcc.ru:10332"
DEFAULT_OUTPUT_PREFIX = "compat-mainnet"


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser for cross-node compatibility checks."""
    parser = argparse.ArgumentParser(
        prog="neo-compat",
        description="Run neo-diff against C# and NeoGo RPC endpoints and compare outcomes.",
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
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory to write both neo-diff JSON reports.",
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
        help="Return success when C# and NeoGo results are identical, even if both fail vectors.",
    )
    parser.add_argument(
        "--ignore-vector",
        action="append",
        default=[],
        help="Vector name to ignore during compatibility comparison (repeatable).",
    )
    parser.add_argument(
        "--ignore-vectors-file",
        type=Path,
        default=None,
        help="Path to newline-delimited vector names to ignore ('#' comments allowed).",
    )
    return parser


def run_neo_diff(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
    """Run neo-diff against one RPC endpoint and store JSON output."""
    command = [
        sys.executable,
        "-m",
        "neo.tools.diff.cli",
        "--vectors",
        str(vectors),
        "--csharp-rpc",
        rpc_url,
        "--output",
        str(output_path),
        "--gas-tolerance",
        str(gas_tolerance),
    ]
    result = subprocess.run(command, check=False)
    return result.returncode


def _load_report(path: Path) -> dict[str, Any]:
    with open(path) as report_file:
        raw_report = json.load(report_file)
    if not isinstance(raw_report, dict):
        raise ValueError(f"Invalid report structure in {path}")
    return raw_report


def _indexed_results(report: dict[str, Any]) -> dict[str, tuple[bool, list[dict[str, Any]]]]:
    return _indexed_results_filtered(report, ignored_vectors=None)


def _indexed_results_filtered(
    report: dict[str, Any],
    ignored_vectors: set[str] | None,
) -> dict[str, tuple[bool, list[dict[str, Any]]]]:
    indexed: dict[str, tuple[bool, list[dict[str, Any]]]] = {}
    results = report.get("results")
    if not isinstance(results, list):
        return indexed

    for entry in results:
        if not isinstance(entry, dict):
            continue
        vector = entry.get("vector")
        if not isinstance(vector, str) or not vector:
            continue
        if ignored_vectors and vector in ignored_vectors:
            continue
        match = bool(entry.get("match", False))
        differences_raw = entry.get("differences")
        differences: list[dict[str, Any]] = []
        if isinstance(differences_raw, list):
            for diff in differences_raw:
                if isinstance(diff, dict):
                    differences.append(diff)
        indexed[vector] = (match, differences)

    return indexed


def compare_report_results(
    csharp_report: dict[str, Any],
    neogo_report: dict[str, Any],
    ignored_vectors: set[str] | None = None,
) -> list[str]:
    """Return vector names where C# and NeoGo report outcomes differ."""
    csharp_results = _indexed_results_filtered(csharp_report, ignored_vectors)
    neogo_results = _indexed_results_filtered(neogo_report, ignored_vectors)

    all_vectors = sorted(set(csharp_results) | set(neogo_results))
    deltas: list[str] = []

    for vector in all_vectors:
        csharp_result = csharp_results.get(vector)
        neogo_result = neogo_results.get(vector)

        if csharp_result is None or neogo_result is None:
            deltas.append(vector)
            continue

        csharp_match, csharp_diffs = csharp_result
        neogo_match, neogo_diffs = neogo_result

        if csharp_match != neogo_match or csharp_diffs != neogo_diffs:
            deltas.append(vector)

    return deltas


def _summary(report: dict[str, Any], ignored_vectors: set[str] | None = None) -> dict[str, int]:
    """Return report summary, optionally excluding specific vector names."""
    summary_raw = report.get("summary")
    errors = 0
    if isinstance(summary_raw, dict):
        raw_errors = summary_raw.get("errors", 0)
        if isinstance(raw_errors, int):
            errors = raw_errors
        elif isinstance(raw_errors, str) and raw_errors.isdigit():
            errors = int(raw_errors)

    indexed = _indexed_results_filtered(report, ignored_vectors)
    total = len(indexed)
    passed = sum(1 for match, _ in indexed.values() if match)
    failed = total - passed
    return {"total": total, "passed": passed, "failed": failed, "errors": errors}


def load_ignored_vectors(
    inline_vectors: Iterable[str] | None,
    vectors_file: Path | None,
) -> set[str]:
    """Load ignored vector names from CLI values and optional file."""
    ignored: set[str] = set()

    if inline_vectors:
        ignored.update(name.strip() for name in inline_vectors if name and name.strip())

    if vectors_file is None:
        return ignored
    if not vectors_file.exists():
        raise FileNotFoundError(f"ignore vectors file not found: {vectors_file}")

    with open(vectors_file, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            ignored.add(line)

    return ignored


def is_strictly_compatible(
    csharp_summary: dict[str, int],
    neogo_summary: dict[str, int],
    vector_deltas: list[str],
) -> bool:
    """Strict compatibility means zero report deltas and zero failures/errors."""
    if vector_deltas:
        return False
    if csharp_summary.get("failed", 0) != 0 or csharp_summary.get("errors", 0) != 0:
        return False
    if neogo_summary.get("failed", 0) != 0 or neogo_summary.get("errors", 0) != 0:
        return False
    return csharp_summary.get("total", 0) == neogo_summary.get("total", 0)


def main(argv: list[str] | None = None) -> int:
    """Run compatibility checks for C# and NeoGo endpoints."""
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        ignored_vectors = load_ignored_vectors(args.ignore_vector, args.ignore_vectors_file)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csharp_output = args.output_dir / f"{args.prefix}-csharp.json"
    neogo_output = args.output_dir / f"{args.prefix}-neogo.json"

    print(f"Running C# reference against: {args.csharp_rpc}")
    csharp_exit = run_neo_diff(args.vectors, args.csharp_rpc, csharp_output, args.gas_tolerance)

    print(f"Running NeoGo endpoint against: {args.neogo_rpc}")
    neogo_exit = run_neo_diff(args.vectors, args.neogo_rpc, neogo_output, args.gas_tolerance)

    if csharp_exit not in (0, 1) or neogo_exit not in (0, 1):
        print("neo-diff command execution failed", file=sys.stderr)
        return 1

    if not csharp_output.exists() or not neogo_output.exists():
        print("neo-diff report output missing", file=sys.stderr)
        return 1

    csharp_report = _load_report(csharp_output)
    neogo_report = _load_report(neogo_output)

    csharp_summary = _summary(csharp_report, ignored_vectors)
    neogo_summary = _summary(neogo_report, ignored_vectors)
    vector_deltas = compare_report_results(csharp_report, neogo_report, ignored_vectors)

    print("\nC# summary:", csharp_summary)
    print("NeoGo summary:", neogo_summary)
    print(f"Vector deltas: {len(vector_deltas)}")
    if ignored_vectors:
        print(f"Ignored vectors: {len(ignored_vectors)}")

    if vector_deltas:
        print("Mismatched vectors:")
        for vector in vector_deltas[:20]:
            print(f"  - {vector}")

    if args.allow_shared_failures:
        return 0 if not vector_deltas else 1

    return 0 if is_strictly_compatible(csharp_summary, neogo_summary, vector_deltas) else 1


if __name__ == "__main__":
    raise SystemExit(main())
