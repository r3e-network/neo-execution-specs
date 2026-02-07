# Testing Guide

This document covers the testing infrastructure for neo-execution-specs.

## Overview

The project uses a multi-layered testing approach:

1. **Unit Tests** - Test individual components
2. **Integration Tests** - Test component interactions
3. **Test Vectors** - Cross-implementation validation
4. **Diff Testing** - Compare with C# reference

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/vm/test_numeric.py

# Run specific test
pytest tests/vm/test_numeric.py::test_add_basic

# Run tests matching pattern
pytest -k "add"
```

### Coverage

```bash
# Run with coverage
pytest --cov=neo --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Categories

```bash
# Run only VM tests
pytest tests/vm/

# Run only native contract tests
pytest tests/native/

# Run only crypto tests
pytest tests/crypto/
```

## Test Structure

```
tests/
├── vm/                    # VM instruction tests
│   ├── test_numeric.py    # Arithmetic operations
│   ├── test_stack.py      # Stack manipulation
│   ├── test_control.py    # Control flow
│   └── ...
├── native/                # Native contract tests
│   ├── test_neo_token.py
│   ├── test_gas_token.py
│   └── ...
├── crypto/                # Cryptography tests
│   ├── test_hash.py
│   ├── test_ecc.py
│   └── ...
├── types/                 # Type tests
├── persistence/           # Storage tests
├── network/               # Network payload tests
├── vectors/               # Test vector framework
└── tools/                 # CLI tool tests
```

## Test Vectors

### Purpose

Test vectors provide a standardized way to validate implementations across different languages. They define inputs and expected outputs in JSON format.

### Vector Format

#### VM Vectors

```json
{
  "name": "ADD_basic",
  "description": "Basic addition: 3 + 5 = 8",
  "pre": {
    "stack": []
  },
  "script": "0x13159e",
  "post": {
    "stack": [8]
  },
  "error": null,
  "gas": null
}
```

Fields:
- `name` - Unique identifier
- `description` - Human-readable description
- `pre.stack` - Initial stack state
- `script` - Hex-encoded script bytes
- `post.stack` - Expected final stack
- `error` - Expected error (null if success)
- `gas` - Expected gas consumption (optional)

#### Crypto Vectors

```json
{
  "name": "SHA256_hello",
  "description": "SHA256 of 'hello'",
  "operation": "SHA256",
  "input": {
    "data": "0x68656c6c6f"
  },
  "output": {
    "hash": "0x2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
  }
}
```

### Vector Locations

As of February 7, 2026, the suite contains `242` raw vectors (`236` runnable by `neo-diff`).

```
tests/vectors/
├── vm/                    # VM instruction vectors
│   ├── arithmetic.json
│   ├── stack.json
│   ├── bitwise.json
│   ├── comparison.json
│   ├── boolean.json
│   ├── compound.json
│   └── protocol_extended.json
├── crypto/                # Crypto vectors
│   ├── hash.json
│   ├── hash_extended.json
│   └── bls12_381.json
├── native/                # Native contract vectors
│   ├── neo_token.json
│   ├── gas_token.json
│   └── native_extended.json
└── state/                 # State transition vectors
```

### Generating Vectors

```bash
# Generate all vectors
python tests/vectors/generate_all.py

# Generate with verification
python tests/vectors/generate_all.py --verify

# Generate specific category
python tests/vectors/vm_generator.py
```

### Validating Vectors

```bash
# Validate all vectors against Python implementation
python tests/vectors/validate.py

# Validate specific file
python tests/vectors/validate.py tests/vectors/vm/arithmetic.json
```

## Adding New Test Vectors

### Step 1: Create Generator

Create or edit a generator file (e.g., `my_generator.py`):

```python
from tests.vectors.generator import VMVector, save_vectors

def generate_my_vectors() -> list[VMVector]:
    vectors = []
    
    # Example: test PUSH1 opcode
    vectors.append(VMVector(
        name="PUSH1_42",
        description="Push integer 42",
        script=bytes([0x00, 0x2a]),  # PUSH1 42
        post_stack=[42],
    ))
    
    return vectors

if __name__ == "__main__":
    vectors = generate_my_vectors()
    save_vectors(vectors, "tests/vectors/vm/my_vectors.json")
```

### Step 2: Register Generator

Add to `generate_all.py`:

```python
from tests.vectors.my_generator import generate_my_vectors

generators = [
    # ... existing generators
    ("vm/my_vectors.json", generate_my_vectors),
]
```

### Step 3: Run and Verify

```bash
python tests/vectors/generate_all.py --verify
```

## Diff Testing

The diff testing framework compares Python spec execution with the C# reference implementation.

### Using neo-diff CLI

```bash
# Run Python-only validation
neo-diff --vectors tests/vectors/vm/ --python-only

# Compare with C# implementation
neo-diff --vectors tests/vectors/vm/ --csharp-rpc http://localhost:10332

# Generate JSON report
neo-diff --vectors tests/vectors/ --output report.json --verbose

# Compare C# vs NeoGo endpoints using shared vectors
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1.neo.org:10332 \
           --neogo-rpc http://rpc3.n3.nspcc.ru:10332
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--vectors, -v` | Path to test vectors (file or directory) |
| `--csharp-rpc, -r` | C# neo-cli RPC URL |
| `--output, -o` | Output JSON report path |
| `--python-only, -p` | Run Python spec only |
| `--gas-tolerance, -g` | Allowed gas difference |
| `--verbose` | Show detailed output |

### Checklist Coverage (Ethereum-style)

Following the `ethereum/execution-spec-tests` model, this repository tracks protocol verification items through a checklist template and enforces 100% item coverage in CI.

```bash
neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md \
             --coverage-manifest tests/vectors/checklist_coverage.json \
             --vectors-root tests/vectors/
```

The command fails if:
- checklist template IDs drift from Python checklist IDs,
- manifest entries drift from checklist IDs,
- manifest references unknown vectors, or
- any checklist item lacks vector/evidence coverage.

### Programmatic Usage

```python
from neo.tools.diff.runner import DiffTestRunner, VectorLoader
from neo.tools.diff.comparator import ResultComparator

# Load vectors
vectors = VectorLoader.load_directory(Path("tests/vectors/vm/"))

# Run tests
runner = DiffTestRunner(python_only=True)
for vector in vectors:
    py_result, _ = runner.run_vector(vector)
    print(f"{vector.name}: {py_result.state}")
```

## Writing Good Tests

### Test Naming

Use descriptive names that indicate what's being tested:

```python
def test_add_positive_integers():
    """ADD with two positive integers."""
    ...

def test_add_negative_overflow():
    """ADD that causes negative overflow."""
    ...

def test_add_max_biginteger():
    """ADD at BigInteger size limit."""
    ...
```

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_push_integer():
    # Arrange
    engine = ExecutionEngine()
    script = ScriptBuilder().emit_push(42).to_array()
    
    # Act
    engine.load_script(script)
    engine.execute()
    
    # Assert
    assert len(engine.result_stack) == 1
    assert engine.result_stack.peek().get_integer() == 42
```

### Edge Cases

Always test edge cases:

```python
# Zero values
def test_add_zero(): ...

# Negative values
def test_add_negative(): ...

# Boundary values
def test_add_max_int(): ...

# Error conditions
def test_add_type_mismatch(): ...
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch

### CI Configuration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[all]"
      - run: pytest --cov=neo
```
