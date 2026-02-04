# Architecture

This document describes the architecture of neo-execution-specs, a Python reference implementation of the Neo N3 protocol.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Wallets   │  │   Ledger    │  │    Native Contracts     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Smart Contract Layer                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              ApplicationEngine                           │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │    │
│  │  │ Syscalls │  │ Interop  │  │ Manifest │  │   NEF   │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                          VM Layer                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              ExecutionEngine (NeoVM)                     │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │    │
│  │  │ OpCodes  │  │  Stack   │  │  Slots   │  │ RefCnt  │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                        Core Layer                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐     │
│  │  Types   │  │  Crypto  │  │    IO    │  │ Persistence  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

### Core Types (`neo.types`)

Basic data types used throughout the codebase:

| Type | Description | C# Equivalent |
|------|-------------|---------------|
| `UInt160` | 20-byte hash (addresses) | `Neo.UInt160` |
| `UInt256` | 32-byte hash (tx/block hashes) | `Neo.UInt256` |
| `BigInteger` | Arbitrary precision integer | `System.Numerics.BigInteger` |
| `ECPoint` | Elliptic curve point | `Neo.Cryptography.ECC.ECPoint` |

### Virtual Machine (`neo.vm`)

The NeoVM implementation with 200+ opcodes:

```
neo/vm/
├── execution_engine.py    # Main VM engine
├── execution_context.py   # Script execution context
├── evaluation_stack.py    # Operand stack
├── reference_counter.py   # GC reference counting
├── slot.py               # Local/argument slots
├── script_builder.py     # Script construction
├── opcode.py             # Opcode definitions
├── types/                # Stack item types
│   ├── stack_item.py     # Base class
│   ├── integer.py        # Integer type
│   ├── byte_string.py    # ByteString type
│   ├── array.py          # Array type
│   ├── map.py            # Map type
│   ├── struct.py         # Struct type
│   └── buffer.py         # Buffer type
└── instructions/         # Opcode implementations
    ├── numeric.py        # ADD, SUB, MUL, etc.
    ├── stack.py          # PUSH, DUP, DROP, etc.
    ├── control.py        # JMP, CALL, RET, etc.
    ├── bitwise.py        # AND, OR, XOR, etc.
    ├── comparison.py     # LT, GT, EQ, etc.
    └── ...
```

### Cryptography (`neo.crypto`)

Cryptographic primitives:

```
neo/crypto/
├── hash.py              # SHA256, RIPEMD160, Hash160, Hash256
├── murmur.py            # Murmur3 hash
├── bloom_filter.py      # Bloom filter
├── merkle_tree.py       # Merkle tree
├── ecc/                 # Elliptic curve cryptography
│   ├── curve.py         # Curve definitions
│   ├── ec_point.py      # Point operations
│   └── ecdsa.py         # ECDSA signatures
├── bls12_381/           # BLS12-381 pairing
│   ├── g1.py            # G1 group
│   ├── g2.py            # G2 group
│   ├── gt.py            # GT group
│   └── scalar.py        # Scalar field
└── ed25519.py           # Ed25519 signatures (optional)
```

### Smart Contracts (`neo.smartcontract`)

Contract execution environment:

```
neo/smartcontract/
├── application_engine.py  # Main execution engine
├── interop_service.py     # System call dispatcher
├── storage_context.py     # Storage access
├── contract_state.py      # Contract state
├── nef_file.py           # NEF format
├── binary_serializer.py   # Stack item serialization
├── json_serializer.py     # JSON serialization
├── manifest/             # Contract manifest
│   ├── contract_manifest.py
│   ├── contract_abi.py
│   └── ...
└── syscalls/             # System call implementations
```

### Native Contracts (`neo.native`)

Built-in system contracts:

| Contract | Hash | Description |
|----------|------|-------------|
| `NeoToken` | `0xef4073...` | NEO governance token |
| `GasToken` | `0xd2a4cf...` | GAS utility token |
| `PolicyContract` | `0xcc5e4e...` | Network policies |
| `ContractManagement` | `0xfffdc9...` | Contract lifecycle |
| `LedgerContract` | `0xda6529...` | Blockchain data |
| `OracleContract` | `0xfe924b...` | Oracle service |
| `RoleManagement` | `0x49cf4e...` | Role-based access |
| `CryptoLib` | `0x726cb6...` | Crypto functions |
| `StdLib` | `0xacce6f...` | Standard library |
| `Notary` | `0xc1e14f...` | Notary service |

### Persistence (`neo.persistence`)

Storage layer:

```
neo/persistence/
├── store.py           # IStore interface
├── snapshot.py        # ISnapshot interface
├── data_cache.py      # Cached data access
├── memory_store.py    # In-memory implementation
└── cloned_cache.py    # Cloned cache for isolation
```

## C# Implementation Mapping

| Python Module | C# Namespace |
|--------------|--------------|
| `neo.vm` | `Neo.VM` |
| `neo.vm.types` | `Neo.VM.Types` |
| `neo.crypto` | `Neo.Cryptography` |
| `neo.smartcontract` | `Neo.SmartContract` |
| `neo.native` | `Neo.SmartContract.Native` |
| `neo.network` | `Neo.Network.P2P.Payloads` |
| `neo.persistence` | `Neo.Persistence` |
| `neo.ledger` | `Neo.Ledger` |
| `neo.wallets` | `Neo.Wallets` |

## Design Principles

### 1. Readability Over Performance

This is a **reference implementation** prioritizing clarity:

```python
# Clear, explicit code
def execute_add(engine: ExecutionEngine) -> None:
    """ADD: Pop two integers, push their sum."""
    b = engine.pop().get_integer()
    a = engine.pop().get_integer()
    result = a + b
    engine.push(Integer(result))
```

### 2. Type Safety

Strong typing with Python type hints:

```python
def get_storage(
    self,
    context: StorageContext,
    key: bytes
) -> Optional[StorageItem]:
    ...
```

### 3. Minimal Dependencies

Core functionality works with Python stdlib only. Optional dependencies for advanced crypto:

- `cryptography` - Ed25519 support
- `pycryptodome` - Keccak256
- `py_ecc` - BLS12-381 pairing

### 4. Test-Driven

Every component has comprehensive tests. Test vectors enable cross-implementation validation.

## Data Flow

### Script Execution

```
Script (bytes)
    │
    ▼
┌─────────────────┐
│ ExecutionEngine │
│  ├─ load_script │
│  ├─ execute     │
│  └─ result_stack│
└─────────────────┘
    │
    ▼
Result (StackItem[])
```

### Contract Invocation

```
Transaction
    │
    ▼
┌───────────────────┐
│ ApplicationEngine │
│  ├─ LoadScript    │
│  ├─ Syscalls      │
│  └─ Storage       │
└───────────────────┘
    │
    ▼
ExecutionResult
  ├─ State (HALT/FAULT)
  ├─ GasConsumed
  ├─ Stack
  └─ Notifications
```

## Extension Points

### Adding New Opcodes

1. Define opcode in `neo/vm/opcode.py`
2. Implement handler in appropriate `instructions/*.py`
3. Register in instruction table
4. Add tests

### Adding New Syscalls

1. Define syscall hash
2. Implement in `neo/smartcontract/syscalls/`
3. Register in `InteropService`
4. Add tests

### Adding New Native Contracts

1. Create class extending `NativeContract`
2. Implement required methods
3. Register contract hash
4. Add tests
