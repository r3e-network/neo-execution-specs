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

# Compare with public Neo mainnet node (v3.9.1)
neo-diff --vectors tests/vectors/vm/ --csharp-rpc http://seed1.neo.org:10332

# Generate JSON report
neo-diff --vectors tests/vectors/ -r http://localhost:10332 -o report.json

# Compare C# vs NeoGo directly
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1.neo.org:10332 \
           --neogo-rpc http://rpc3.n3.nspcc.ru:10332
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

## RPC Compatibility Notes

- Neo v3.9.1 `invokescript` endpoints expect the script parameter as **base64**.
- Some other RPC providers accept **hex**.
- `neo-diff` automatically tries base64 first and falls back to hex when needed.

## Non-VM Vector Support

`neo-diff` can now load and execute collection-style vectors in addition to raw VM script vectors.

### Supported categories

- `vm/*` - executed via `invokescript` and Python VM execution
- `native/*` - executed via `invokefunction` against native contracts
- `crypto/hash.json` - supports `SHA256`, `RIPEMD160`, `HASH160`, `HASH256`

### Current skip rules

- `crypto/bls12_381.json` vectors are skipped because BLS operations are not yet wired into the diff runner.
- `state/state_transitions.json` vectors without an executable transaction script are skipped.

Skipped vectors are reported as warnings during load.

### Native RPC behavior

- Native contract hashes are resolved from node RPC via `getnativecontracts`.
- Contract calls use `invokefunction` with parameter encoding based on vector argument types.
