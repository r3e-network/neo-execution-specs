# Neo N3 Execution Specs

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1024%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python reference implementation of the Neo N3 protocol, prioritizing **readability** over performance.

## Overview

This project provides an executable specification for:
- **NeoVM** - Neo Virtual Machine with all 200+ opcodes
- **ApplicationEngine** - Smart contract execution environment
- **Native Contracts** - All 10 built-in system contracts
- **Cryptography** - ECDSA, Ed25519, BLS12-381, hash functions
- **Persistence** - Storage layer with snapshots and caching

## Status

| Component | Status | Tests |
|-----------|--------|-------|
| VM Core | ✅ Complete | 400+ |
| Cryptography | ✅ Complete | 150+ |
| Native Contracts | ✅ Complete | 200+ |
| Storage Layer | ✅ Complete | 100+ |
| Network Types | ✅ Complete | 150+ |
| **Total** | **Production Ready** | **1037** |

## Installation

```bash
# Basic installation
pip install neo-execution-specs

# With crypto dependencies (recommended)
pip install neo-execution-specs[crypto]

# Full development installation
pip install neo-execution-specs[all]
```

## Development

```bash
# Clone repository
git clone https://github.com/neo-project/neo-execution-specs.git
cd neo-execution-specs

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[all]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=neo --cov-report=html
```

## Project Structure

```
src/neo/
├── vm/                 # NeoVM - Virtual Machine
│   ├── execution_engine.py
│   ├── instructions/   # All opcode implementations
│   └── types/          # Stack item types
├── crypto/             # Cryptography
│   ├── ecc/            # Elliptic curve operations
│   ├── bls12_381/      # BLS12-381 pairing
│   └── ed25519.py      # Ed25519 signatures
├── smartcontract/      # Smart Contract Layer
│   ├── application_engine.py
│   ├── manifest/       # Contract manifests
│   └── syscalls/       # System calls
├── native/             # Native Contracts
│   ├── neo_token.py    # NEO token
│   ├── gas_token.py    # GAS token
│   └── ...             # Other native contracts
├── network/            # Network Types
│   └── payloads/       # Block, Transaction, etc.
└── persistence/        # Storage Layer
    ├── memory_store.py
    └── snapshot.py
```

## Quick Example

```python
from neo.vm import ExecutionEngine, ScriptBuilder
from neo.vm.opcode import OpCode

# Build a simple script
sb = ScriptBuilder()
sb.emit_push(10)
sb.emit_push(20)
sb.emit(OpCode.ADD)
script = sb.to_array()

# Execute
engine = ExecutionEngine()
engine.load_script(script)
engine.execute()

# Get result
result = engine.result_stack.pop()
print(f"10 + 20 = {result.get_integer()}")  # Output: 10 + 20 = 30
```

## Optional Dependencies

| Package | Purpose |
|---------|---------|
| `cryptography` | Ed25519 signature support |
| `pycryptodome` | Keccak256 hash function |
| `py_ecc` | BLS12-381 pairing operations |

Install with: `pip install neo-execution-specs[crypto]`

## Documentation

- [ROADMAP.md](ROADMAP.md) - Implementation progress and phases
- [VERIFICATION-REPORT.md](VERIFICATION-REPORT.md) - Quality assessment

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## References

- [Neo N3 Documentation](https://docs.neo.org/)
- [Neo GitHub](https://github.com/neo-project/neo)
- [Neo VM](https://github.com/neo-project/neo-vm)
