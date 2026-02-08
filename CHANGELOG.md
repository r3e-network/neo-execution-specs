# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Deep vector expansion**
- **Protocol-surface matrix expansion**
  - Added deep VM control-flow vectors (`tests/vectors/vm/control_flow_deep.json`) for long jump families, CALL/CALL_L/CALLA/PUSHA, TRY/ENDTRY long-offset paths, and ABORTMSG/ASSERTMSG behavior.
  - Added deep VM memory/slot/compound vectors (`tests/vectors/vm/memory_slot_compound_deep.json`) for MEMCPY bounds, slot lifecycle faults, NEWARRAY_T defaults, and PACK/PACKSTRUCT/UNPACK semantics.
  - Added hash payload matrix vectors (`tests/vectors/crypto/hash_matrix.json`) across boundary payload classes.
  - Added native matrix vectors (`tests/vectors/native/native_matrix.json`) for StdLib radix/base64/memory-compare and CryptoLib seed combinations.
  - Added deeper executable state vectors (`tests/vectors/state/executable_state_deep.json`) for call/exception/memory-script execution paths.

  - Added VM fault-path vector suite (`tests/vectors/vm/faults_extended.json`) for boundary and invalid-argument behavior.
  - Added native deep vector suite (`tests/vectors/native/native_deep.json`) and crypto deep suite (`tests/vectors/crypto/hash_deep.json`).
  - Added executable state vectors (`tests/vectors/state/executable_state_stubs.json`) to keep state-script lane active in diff validation.
  - Added `tests/tools/test_non_vm_vector_expectations.py` to enforce declared expected outputs for native/crypto vectors.

- **Full-surface protocol checklist**
  - Expanded Ethereum-style Neo v3.9.1 checklist to cover VM, smart contracts, native contracts, crypto, network payloads, persistence, ledger, wallets, and cross-client validation.
  - Added `docs/verification/neo-n3-full-surface-matrix.md` for verification scope governance.

- **Tri-client compatibility tooling**
  - Added `neo-multicompat` CLI for C# vs NeoGo vs neo-rs vector parity checks.
  - Added unit tests for triplet report comparison logic.

- **Workflow integration**
  - Extended diff workflow with optional `workflow_dispatch` tri-client lane using a supplied neo-rs RPC endpoint.

### Changed

- Fixed VM `MEMCPY` destination bounds check to use buffer length (`len(dst)`) and added dedicated splice instruction tests.
- Raised corpus depth gates to enforce broader VM/native/crypto/state surface thresholds and advanced opcode floor checks.

- Aligned PolicyContract vector defaults with observed Neo v3.9.1 baseline values (`FeePerByte=20`, `ExecFeeFactor=1`, `StoragePrice=1000`).

## [0.1.0] - 2024-02-04

### Added

- **VM Core**
  - Complete NeoVM implementation with 200+ opcodes
  - ExecutionEngine with full instruction support
  - EvaluationStack and Slot system
  - Reference counter for GC
  - TRY/CATCH/FINALLY exception handling
  - CALLT instruction for method token calls

- **Cryptography**
  - Hash functions: SHA256, RIPEMD160, Hash160, Hash256
  - ECDSA signatures (secp256r1, secp256k1)
  - Ed25519 signatures (optional dependency)
  - BLS12-381 pairing operations
  - Merkle tree with proof generation
  - Bloom filter implementation
  - Murmur3 hash

- **Native Contracts**
  - NeoToken - NEO governance token
  - GasToken - GAS utility token
  - PolicyContract - Network policies
  - ContractManagement - Contract lifecycle
  - LedgerContract - Blockchain data access
  - OracleContract - Oracle service
  - RoleManagement - Role-based access
  - CryptoLib - Cryptographic functions
  - StdLib - Standard library
  - Notary - Notary service

- **Smart Contract Layer**
  - ApplicationEngine with syscall support
  - Contract manifest and ABI
  - NEF file format
  - Storage context and operations
  - Binary and JSON serializers

- **Persistence**
  - IStore and ISnapshot interfaces
  - MemoryStore implementation
  - DataCache with caching
  - ClonedCache for isolation

- **Network Types**
  - Block, Transaction, Header
  - Witness and Signer
  - WitnessScope and WitnessCondition
  - Transaction attributes

- **CLI Tools**
  - `neo-diff` - Diff testing framework
  - `neo-t8n` - State transition tool

- **Testing**
  - 1037 unit tests
  - Test vector framework
  - Integration tests

### Notes

- Target: Neo N3 v3.9.1
- Python 3.11+ required
- Optional crypto dependencies for advanced features
