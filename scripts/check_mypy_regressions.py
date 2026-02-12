"""Guard against mypy error-count regressions while backlog is reduced."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SUMMARY_PATTERN = re.compile(r"Found (?P<count>\d+) errors? in \d+ files?")


def parse_mypy_error_count(output: str, returncode: int) -> int | None:
    """Parse mypy error count from command output."""
    if returncode == 0:
        return 0

    match = SUMMARY_PATTERN.search(output)
    if match is None:
        return None

    return int(match.group("count"))


def check_baseline(current_errors: int, baseline_errors: int) -> bool:
    """Return True when current mypy errors are at or below baseline."""
    return current_errors <= baseline_errors


def read_baseline_errors(path: Path) -> int:
    """Read baseline error count from a plain text file."""
    raw = path.read_text(encoding="utf-8").strip()
    if not raw.isdigit():
        raise ValueError(f"Baseline file {path} must contain a non-negative integer")
    return int(raw)


def run_mypy(target: str, ignore_missing_imports: bool) -> tuple[int, str]:
    """Execute mypy and return (exit_code, combined_output)."""
    command = [sys.executable, "-m", "mypy", target]
    if ignore_missing_imports:
        command.append("--ignore-missing-imports")

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return result.returncode, output


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser for mypy regression guard."""
    parser = argparse.ArgumentParser(
        prog="check-mypy-regressions",
        description="Fail when mypy error count exceeds configured baseline.",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=Path("scripts/mypy-error-baseline.txt"),
        help="Path to file containing maximum allowed mypy error count.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="src/neo",
        help="Mypy target path/module (default: src/neo).",
    )
    parser.add_argument(
        "--ignore-missing-imports",
        action="store_true",
        default=True,
        help="Pass --ignore-missing-imports to mypy (default: enabled).",
    )
    parser.add_argument(
        "--no-ignore-missing-imports",
        dest="ignore_missing_imports",
        action="store_false",
        help="Disable --ignore-missing-imports.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run mypy and compare current error count against baseline."""
    args = create_parser().parse_args(argv)

    baseline_errors = read_baseline_errors(args.baseline_file)
    returncode, output = run_mypy(
        target=args.target,
        ignore_missing_imports=args.ignore_missing_imports,
    )

    if output:
        print(output, end="" if output.endswith("\n") else "\n")

    current_errors = parse_mypy_error_count(output=output, returncode=returncode)
    if current_errors is None:
        print("Could not parse mypy error count from output.")
        return 2

    if check_baseline(current_errors=current_errors, baseline_errors=baseline_errors):
        delta = baseline_errors - current_errors
        print(
            "Mypy baseline check passed: "
            f"current={current_errors}, baseline={baseline_errors}, improvement={delta}."
        )
        return 0

    print(
        "Mypy regression detected: "
        f"current={current_errors} exceeds baseline={baseline_errors}."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
