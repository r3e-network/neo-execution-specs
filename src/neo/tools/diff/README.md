# Neo Diff Testing Framework

Compare Python spec execution results with C# neo-cli implementation.

## Installation

```bash
cd /home/neo/git/neo-execution-specs
pip install -e .
```

## Quick Start

```bash
# Python-only mode (no C# comparison)
neo-diff --vectors tests/vectors/ --python-only

# Compare with C# neo-cli
neo-diff --vectors tests/vectors/ --csharp-rpc http://localhost:10332

# Generate JSON report
neo-diff --vectors tests/vectors/ -r http://localhost:10332 -o report.json
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--vectors, -v` | Path to test vectors (file or directory) |
| `--csharp-rpc, -r` | C# neo-cli RPC URL |
| `--output, -o` | Output JSON report path |
| `--python-only, -p` | Run Python spec only |
| `--gas-tolerance, -g` | Allowed gas difference |
| `--verbose` | Show detailed output |

## Test Vector Format

```json
{
  "name": "test_name",
  "script": "hex_encoded_script",
  "description": "Test description",
  "expected_state": "HALT",
  "expected_stack": [
    {"type": "Integer", "value": 42}
  ]
}
```

## Architecture

- `runner.py` - Test execution (Python + C# RPC)
- `comparator.py` - Result comparison
- `reporter.py` - Report generation
- `cli.py` - Command-line interface
- `models.py` - Data models
