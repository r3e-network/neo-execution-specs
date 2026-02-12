# Neo N3 Execution Specs[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1400%2B%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python reference implementation of the Neo N3 protocol, prioritizing **readability** over performance.

## What is This?

This project provides an **executable specification** for Neo N3, similar to Ethereum's [execution-specs](https://github.com/ethereum/execution-specs). It serves as:

- 📖 **Reference Implementation** - Clear, readable code that documents the protocol
- ✅ **Validation Tool** - Cross-check other implementations via diff testing
- 🧪 **Test Vector Generator** - Create standardized test cases
- 📚 **Learning Resource** - Understand Neo internals

## Features

| Component | Status | Tests |
|-----------|--------|-------|
| NeoVM (200+ opcodes) | ✅ Complete | 400+ |
| Cryptography | ✅ Complete | 150+ |
| Native Contracts (10) | ✅ Complete | 200+ |
| Storage Layer | ✅ Complete | 100+ |
| Network Types | ✅ Complete | 150+ |
| **Total** | **Production Ready** | **1400+** |

## Installation

```bash
# Basic installation
pip install neo-execution-specs

# With optional BLS dependencies
pip install neo-execution-specs[crypto]

# Full development installation
pip install neo-execution-specs[all]
```

## Quick Start

### Execute a Simple Script

```python
from neo.vm import ExecutionEngine, ScriptBuilder
from neo.vm.opcode import OpCode

# Build script: 10 + 20
sb = ScriptBuilder()
sb.emit_push(10)
sb.emit_push(20)
sb.emit(OpCode.ADD)

# Execute
engine = ExecutionEngine()
engine.load_script(sb.to_array())
engine.execute()

# Get result
result = engine.result_stack.pop()
print(f"10 + 20 = {result.get_integer()}")  # Output: 30
```

### Use Cryptographic Functions

```python
from neo.crypto import hash

data = b"Hello, Neo!"
print(f"SHA256: {hash.sha256(data).hex()}")
print(f"Hash160: {hash.hash160(data).hex()}")
```

## CLI Tools

### neo-diff - Diff Testing

Compare Python spec execution with C# reference:

```bash
# Validate test vectors (Python only)
neo-diff --vectors tests/vectors/vm/ --python-only

# Compare with C# neo-cli
neo-diff --vectors tests/vectors/ --csharp-rpc http://localhost:10332

# Compare C# vs NeoGo compatibility (strict, MainNet)
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1.neo.org:10332 \
           --neogo-rpc http://rpc3.n3.nspcc.ru:10332

# Compare C# vs NeoGo compatibility (strict, TestNet)
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1t5.neo.org:20332 \
           --neogo-rpc http://rpc.t5.n3.nspcc.ru:20332

# Compare C# vs NeoGo vs neo-rs (strict triplet)
neo-multicompat --vectors tests/vectors/ \
                --csharp-rpc http://seed1.neo.org:10332 \
                --neogo-rpc http://rpc3.n3.nspcc.ru:10332 \
                --neo-rs-rpc http://127.0.0.1:40332

# CI matrix parity gate lives in .github/workflows/diff.yml
# (validates protocol fields + vector compatibility for MainNet/TestNet)

# Enforce Ethereum-style checklist coverage gates
neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md \
             --coverage-manifest tests/vectors/checklist_coverage.json \
             --vectors-root tests/vectors/

# Validate non-VM declared expected outputs
pytest tests/tools/test_non_vm_vector_expectations.py -q
```

### Local neo-rs helper scripts

For local deep-dive validation against a running neo-rs RPC node:

```bash
python scripts/neo_rs_vector_runner.py tests/vectors/vm/control_flow.json --show-failures
python scripts/neo_rs_batch_diff.py --vectors-dir tests/vectors --reports-dir reports/neo-rs-batch
```

See `scripts/README.md` for full options and operational guidance.

### neo-t8n - State Transition

Ethereum-style state transition tool:

```bash
neo-t8n --input-alloc alloc.json \
        --input-txs txs.json \
        --input-env env.json \
        --output-result result.json
```

## Development

```bash
# Clone repository
git clone https://github.com/neo-project/neo-execution-specs.git
cd neo-execution-specs

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[all]"

# Run tests
pytest

# Run with coverage
pytest --cov=neo --cov-report=html
```

## Project Structure

```
src/neo/
├── vm/              # NeoVM - Virtual Machine
├── crypto/          # Cryptography (ECC, BLS, hashes)
├── smartcontract/   # ApplicationEngine, syscalls
├── native/          # 10 native contracts
├── network/         # Block, Transaction, etc.
├── persistence/     # Storage layer
├── types/           # UInt160, UInt256, BigInteger
└── tools/           # CLI tools (diff, t8n)
```

## Documentation

- [Architecture](docs/architecture.md) - System design and module structure
- [API Reference](docs/api.md) - Main APIs and examples
- [Testing Guide](docs/testing.md) - Test vectors and diff testing
- [Production Readiness](docs/production-readiness.md) - Release quality gates and checklist
- [Script Helpers](scripts/README.md) - Local neo-rs validation utilities
- [Contributing](CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Version history
- [Roadmap](ROADMAP.md) - Implementation progress
- [Full-Surface Matrix](docs/verification/neo-n3-full-surface-matrix.md) - Ethereum-style full Neo N3 verification scope

## Dependency Notes

| Package | Purpose |
|---------|---------|
| `cryptography` | Included by default (Ed25519 signatures) |
| `pycryptodome` | Included by default (Keccak256 hash) |
| `py_ecc` | Optional via `[crypto]` (BLS12-381 pairing) |

Install with: `pip install neo-execution-specs[crypto]`

## License

MIT License - see [LICENSE](LICENSE) for details.

## References

- [Neo N3 Documentation](https://docs.neo.org/)
- [Neo GitHub](https://github.com/neo-project/neo)
- [Neo VM](https://github.com/neo-project/neo-vm)
- [Ethereum Execution Specs](https://github.com/ethereum/execution-specs)
