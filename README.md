# Neo N3 Execution Specs

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/r3e-network/neo-execution-specs/actions/workflows/test.yml/badge.svg)](https://github.com/r3e-network/neo-execution-specs/actions/workflows/test.yml)
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
| Native Contracts (11) | ✅ Complete | 200+ |
| Storage Layer | ✅ Complete | 100+ |
| Network Types | ✅ Complete | 150+ |
| **Total** | **Release-Gated** | **1543+** |

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

# Compare with live C# endpoint while ignoring governance-mutated PolicyContract
# read values (getFeePerByte/getExecFeeFactor/getStoragePrice) only
neo-diff --vectors tests/vectors/ \
         --csharp-rpc http://seed1.neo.org:10332 \
         --allow-policy-governance-drift

# Compare C# vs NeoGo compatibility (strict, MainNet)
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1.neo.org:10332 \
           --neogo-rpc http://rpc3.n3.nspcc.ru:10332

# Same check with known NeoGo TRY/ENDTRY deltas ignored (5 vectors)
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1.neo.org:10332 \
           --neogo-rpc http://rpc3.n3.nspcc.ru:10332 \
           --ignore-vectors-file docs/verification/neogo-0.116-known-deltas.txt

# Compare C# vs NeoGo compatibility (strict, TestNet)
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1t5.neo.org:20332 \
           --neogo-rpc http://rpc.t5.n3.nspcc.ru:20332

# Compare C# vs NeoGo vs neo-rs (strict triplet)
neo-multicompat --vectors tests/vectors/ \
                --csharp-rpc http://seed1.neo.org:10332 \
                --neogo-rpc http://rpc3.n3.nspcc.ru:10332 \
                --neo-rs-rpc http://127.0.0.1:40332

# Triplet with explicit ignore list
neo-multicompat --vectors tests/vectors/ \
                --csharp-rpc http://seed1.neo.org:10332 \
                --neogo-rpc http://rpc3.n3.nspcc.ru:10332 \
                --neo-rs-rpc http://127.0.0.1:40332 \
                --ignore-vectors-file docs/verification/neogo-0.116-known-deltas.txt

# CI matrix parity gate lives in .github/workflows/diff.yml
# (validates protocol fields + vector compatibility for MainNet/TestNet)
# Scheduled NeoGo endpoint drift probe lives in
# .github/workflows/neogo-endpoint-matrix.yml

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

### NeoGo endpoint matrix helper

For repeatable public NeoGo endpoint delta checks (MainNet + TestNet):

```bash
python3 scripts/neogo_endpoint_matrix.py \
  --output-dir reports/compat-endpoint-matrix \
  --prefix neogo-endpoint-matrix
```

### Native surface parity helper

Validate local native contract surface against live Neo C# RPC:

```bash
python3 scripts/check_native_surface_parity.py \
  --rpc-url http://seed1.neo.org:10332 \
  --json-output reports/native-surface-mainnet.json
```

### neo-t8n - State Transition

Ethereum-style state transition tool:

```bash
neo-t8n --input-alloc alloc.json \
        --input-txs txs.json \
        --input-env env.json \
        --output-result result.json \
        --output-alloc alloc-out.json
# Add --strict to fail fast on first tx validation/execution error
```

`result.json` includes per-tx `vmState`, `gasConsumed`, typed `stack`, and runtime `notifications`.
Malformed tx input (including tx-count overflow, malformed tx object/field types, bad/empty/oversized scripts, unsigned tx-size overflow, nonce/validUntil bounds, signer count/scope/list-bound errors, and witness-rule shape/limit errors) is reported as per-tx `FAULT` receipts; later txs still execute in the same run.

## Development

```bash
# Clone repository
git clone https://github.com/r3e-network/neo-execution-specs.git
cd neo-execution-specs

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[all]"
pip install build twine

# Core quality gates
ruff check src tests scripts
python scripts/check_mypy_regressions.py --baseline-file scripts/mypy-error-baseline.txt
pytest
python scripts/check_release_metadata.py
rm -rf dist build
python -m build --sdist --wheel
twine check dist/*
```

## Production Snapshot (2026-02-19 UTC)

- Live C# 3.9.1 strict vectors (MainNet public endpoint): `402/405` (3 `PolicyContract` value deltas).
- Live policy values currently observed on MainNet/TestNet: `20 / 1 / 1000` for `getFeePerByte / getExecFeeFactor / getStoragePrice`.
- NeoGo strict delta set remains at 5 TRY/ENDTRY vectors on MainNet and on TestNet strict rerun; one TestNet strict run observed a transient extra `ASSERTMSG_false_fault` delta.
- NeoGo endpoint matrix checks now track user-agent by stable token (`NEO-GO:`), not a pinned patch version.
- Native contract surface parity vs live C# is clean on both MainNet and TestNet (`11/11` contracts with zero mismatches).
- Tri-client status: local `neo-rs` endpoints in this environment return connection errors, so tri-client parity is not claimable yet.

Evidence:
- `docs/verification/neogo-0.116-validation-2026-02-16.md`
- `docs/verification/neogo-0.116-known-deltas.txt`
- `docs/verification/live-validation-2026-02-19.md`

## Project Structure

```
src/neo/
├── vm/              # NeoVM - Virtual Machine
├── crypto/          # Cryptography (ECC, BLS, hashes)
├── smartcontract/   # ApplicationEngine, syscalls
├── native/          # 11 native contracts
├── network/         # Block, Transaction, etc.
├── persistence/     # Storage layer
├── types/           # UInt160, UInt256, BigInteger
└── tools/           # CLI tools (diff, t8n)
```

## Documentation

- [Architecture](docs/architecture.md) - System design and module structure
- [Execution Spec](docs/execution-spec.md) - Canonical Neo v3.9.1 execution profile and transition semantics
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
