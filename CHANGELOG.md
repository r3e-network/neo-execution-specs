# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
