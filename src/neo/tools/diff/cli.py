"""Command-line interface for diff testing framework."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from neo.tools.diff.runner import DiffTestRunner, VectorLoader
from neo.tools.diff.comparator import ResultComparator, ComparisonResult
from neo.tools.diff.reporter import DiffReporter


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="neo-diff",
        description="Compare Neo Python spec with C# implementation",
    )
    
    parser.add_argument(
        "--vectors", "-v",
        type=Path,
        required=True,
        help="Path to test vectors (file or directory)",
    )
    
    parser.add_argument(
        "--csharp-rpc", "-r",
        type=str,
        default=None,
        help="C# neo-cli RPC URL (e.g., http://localhost:10332)",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output JSON report path",
    )
    
    parser.add_argument(
        "--python-only", "-p",
        action="store_true",
        help="Run Python spec only (no C# comparison)",
    )
    
    parser.add_argument(
        "--gas-tolerance", "-g",
        type=int,
        default=0,
        help="Allowed gas difference tolerance",
    )

    parser.add_argument(
        "--allow-policy-governance-drift",
        action="store_true",
        help=(
            "Ignore stack[0] value differences for PolicyContract "
            "getFeePerByte/getExecFeeFactor/getStoragePrice native vectors."
        ),
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    
    return parser


def run_diff_tests(args: argparse.Namespace) -> int:
    """Run diff tests with given arguments."""
    # Load vectors
    vectors_path = args.vectors
    if vectors_path.is_file():
        vectors = VectorLoader.load_file(vectors_path)
    elif vectors_path.is_dir():
        vectors = list(VectorLoader.load_directory(vectors_path))
    else:
        print(f"Error: {vectors_path} not found", file=sys.stderr)
        return 1
    
    if not vectors:
        print("No test vectors found", file=sys.stderr)
        return 1
    
    print(f"Loaded {len(vectors)} test vectors")
    
    # Initialize components
    runner = DiffTestRunner(
        csharp_rpc=args.csharp_rpc,
        python_only=args.python_only,
    )
    comparator = ResultComparator(
        gas_tolerance=args.gas_tolerance,
        allow_policy_governance_drift=getattr(args, "allow_policy_governance_drift", False),
    )
    reporter = DiffReporter()
    
    return _execute_tests(runner, comparator, reporter, vectors, args)


def _execute_tests(runner, comparator, reporter, vectors, args) -> int:
    """Execute tests and generate report."""
    for vector in vectors:
        if args.verbose:
            print(f"Running: {vector.name}...", end=" ")
        
        py_result, cs_result = runner.run_vector(vector)
        
        if args.python_only or cs_result is None:
            # Python-only mode
            expected_state = vector.expected_state or "HALT"
            result = ComparisonResult(
                vector_name=vector.name,
                is_match=py_result.state == expected_state,
                python_result=py_result,
            )
            reporter.add_result(result)
            if args.verbose:
                status = "OK" if py_result.state == expected_state else py_result.state
                print(status)
        else:
            # Compare results
            result = comparator.compare(
                vector.name,
                py_result,
                cs_result,
                vector_metadata=vector.metadata,
            )
            reporter.add_result(result)
            if args.verbose:
                print("PASS" if result.is_match else "FAIL")
    
    return _output_report(reporter, args)


def _output_report(reporter, args) -> int:
    """Output the final report."""
    # Write JSON report if requested
    if args.output:
        reporter.write_json(args.output)
        print(f"\nReport written to: {args.output}")
    
    # Write text summary
    print()
    reporter.write_text(sys.stdout)
    
    # Return exit code
    return 0 if reporter.report.failed == 0 and reporter.report.errors == 0 else 1


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    return run_diff_tests(args)


if __name__ == "__main__":
    sys.exit(main())
