"""Neo t8n CLI interface.

Command-line interface for the state transition tool.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def load_json_file(path: str) -> dict:
    """Load JSON from file or stdin."""
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r") as f:
        return json.load(f)


def write_json_file(path: str, data: dict) -> None:
    """Write JSON to file or stdout."""
    if path == "-":
        json.dump(data, sys.stdout, indent=2)
        print()
    else:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="neo-t8n",
        description="Neo N3 state transition tool",
    )
    
    # Input files
    parser.add_argument(
        "--input-alloc",
        default="alloc.json",
        help="Input allocation file (default: alloc.json)",
    )
    parser.add_argument(
        "--input-txs",
        default="txs.json",
        help="Input transactions file (default: txs.json)",
    )
    parser.add_argument(
        "--input-env",
        default="env.json",
        help="Input environment file (default: env.json)",
    )
    
    return parser


def add_output_args(parser: argparse.ArgumentParser) -> None:
    """Add output arguments to parser."""
    parser.add_argument(
        "--output-result",
        default="result.json",
        help="Output result file (default: result.json)",
    )
    parser.add_argument(
        "--output-alloc",
        default="alloc-out.json",
        help="Output allocation file (default: alloc-out.json)",
    )
    parser.add_argument(
        "--output-body",
        help="Output body file (optional)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )


def main(args: Optional[list] = None) -> int:
    """Main entry point."""
    from neo.tools.t8n.t8n import T8N
    
    parser = create_parser()
    add_output_args(parser)
    opts = parser.parse_args(args)
    
    try:
        # Load inputs
        alloc = load_json_file(opts.input_alloc)
        txs = load_json_file(opts.input_txs)
        env = load_json_file(opts.input_env)
        
        if opts.verbose:
            print(f"Loaded {len(alloc)} accounts", file=sys.stderr)
            print(f"Loaded {len(txs)} transactions", file=sys.stderr)
        
        # Run t8n
        t8n = T8N(alloc=alloc, env=env, txs=txs)
        output = t8n.run()
        
        # Write outputs
        write_json_file(opts.output_result, output.result.to_dict())
        write_json_file(opts.output_alloc, output.alloc)
        
        if opts.verbose:
            print(f"Gas used: {output.result.gas_used}", file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
