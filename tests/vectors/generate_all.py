#!/usr/bin/env python3
"""Main Test Vector Generation Script.

Usage:
    python generate_all.py [--verify]
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


# Import all generators
from vm_generator import generate_arithmetic_vectors
from stack_generator import generate_stack_vectors
from bitwise_generator import generate_bitwise_vectors
from comparison_generator import generate_comparison_vectors
from boolean_generator import generate_boolean_vectors
from compound_generator import generate_compound_vectors
from crypto_generator import generate_hash_vectors
from bls_generator import generate_bls_vectors
from native_generator import generate_neo_token_vectors, generate_gas_token_vectors
from state_generator import generate_state_vectors


def generate_all(output_dir: Path, verify: bool = False):
    """Generate all test vectors."""
    print(f"Generating test vectors to {output_dir}")
    print("=" * 60)
    
    collections = [
        # VM vectors
        generate_arithmetic_vectors(),
        generate_stack_vectors(),
        generate_bitwise_vectors(),
        generate_comparison_vectors(),
        generate_boolean_vectors(),
        generate_compound_vectors(),
        # Crypto vectors
        generate_hash_vectors(),
        generate_bls_vectors(),
        # Native contract vectors
        generate_neo_token_vectors(),
        generate_gas_token_vectors(),
        # State vectors
        generate_state_vectors(),
    ]
    
    total_vectors = 0
    for collection in collections:
        filepath = collection.save(output_dir)
        total_vectors += len(collection.vectors)
        
        if verify:
            verify_json(filepath)
    
    print("=" * 60)
    print(f"Total: {total_vectors} vectors in {len(collections)} files")
    return total_vectors


def verify_json(filepath: Path):
    """Verify JSON file is valid."""
    try:
        with open(filepath) as f:
            json.load(f)
        print(f"  ✓ Valid JSON: {filepath.name}")
        return True
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {filepath.name} - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate Neo test vectors")
    parser.add_argument("--verify", action="store_true", help="Verify generated JSON")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent,
                        help="Output directory")
    args = parser.parse_args()
    
    generate_all(args.output, args.verify)


if __name__ == "__main__":
    main()
