# Neo N3 v3.9.1 Execution Specs - Complete Implementation Roadmap

## Target: Full Neo N3 v3.9.1 Specification

This document tracks the complete implementation of Neo N3 execution specifications in Python,
following the style of Ethereum's execution-specs project.

## Current Progress

### ✅ Completed (Phase 1 - Foundation)
- [x] Basic types (UInt160, UInt256, BigInteger)
- [x] VM Stack Item types (Integer, ByteString, Array, Map, Struct, Buffer, Boolean, Null)
- [x] Evaluation Stack
- [x] Reference Counter
- [x] Slot system
- [x] Script Builder
- [x] Basic Execution Engine
- [x] Opcode definitions
- [x] Basic instruction categories (numeric, stack, control flow, bitwise, comparison, compound, splice, slot, constants, types)
- [x] Crypto primitives (hash functions)
- [x] Contract structures (NEF, Manifest, ABI) - scaffolding
- [x] Native contracts - scaffolding
- [x] ApplicationEngine - scaffolding
- [x] Syscalls framework - scaffolding

## Implementation Phases

### Phase 2: Complete VM Layer
- [ ] All 200+ opcodes fully implemented
- [ ] Exception handling (TRY/CATCH/FINALLY)
- [ ] ExecutionContext complete
- [ ] JumpTable optimization
- [ ] Debugger support
- [ ] VM limits enforcement

### Phase 3: Complete Type System
- [ ] StackItem serialization/deserialization
- [ ] InteropInterface type
- [ ] Pointer type
- [ ] Type conversion rules
- [ ] Deep copy semantics

### Phase 4: Cryptography
- [ ] ECC (secp256r1, secp256k1)
- [ ] ECDSA signatures
- [ ] Ed25519
- [ ] BLS12-381
- [ ] Merkle trees
- [ ] Bloom filters
- [ ] Murmur hash

### Phase 5: Smart Contract Core
- [ ] Complete ApplicationEngine
- [ ] All syscalls
- [ ] Contract deployment
- [ ] Contract invocation
- [ ] Storage system
- [ ] Iterators
- [ ] Binary serializer
- [ ] JSON serializer

### Phase 6: Native Contracts (Complete)
- [ ] NeoToken (full implementation)
- [ ] GasToken (full implementation)
- [ ] PolicyContract (full implementation)
- [ ] ContractManagement (full implementation)
- [ ] LedgerContract (full implementation)
- [ ] OracleContract (full implementation)
- [ ] RoleManagement (full implementation)
- [ ] CryptoLib (full implementation)
- [ ] StdLib (full implementation)
- [ ] Notary (full implementation)

### Phase 7: Network Types
- [ ] Block
- [ ] Transaction
- [ ] Header
- [ ] Witness
- [ ] Signers
- [ ] Transaction attributes
- [ ] Cosigners
- [ ] WitnessScope
- [ ] WitnessCondition

### Phase 8: Persistence Layer
- [ ] IStore interface
- [ ] ISnapshot interface
- [ ] DataCache
- [ ] StoreCache
- [ ] ClonedCache
- [ ] MemoryStore

### Phase 9: Ledger
- [ ] Blockchain state
- [ ] Block processing
- [ ] Transaction verification
- [ ] MemoryPool
- [ ] Header cache

### Phase 10: Wallet (Optional for specs)
- [ ] Account
- [ ] KeyPair
- [ ] WalletAccount
- [ ] NEP-6 wallet

### Phase 11: Testing & Validation
- [ ] Unit tests for all components
- [ ] Integration tests
- [ ] Conformance tests against C# implementation
- [ ] Property-based testing

## File Structure Target

```
src/neo/
├── __init__.py
├── exceptions.py
├── protocol_settings.py
├── types/
│   ├── __init__.py
│   ├── uint160.py
│   ├── uint256.py
│   ├── big_integer.py
│   └── ecpoint.py
├── crypto/
│   ├── __init__.py
│   ├── hash.py
│   ├── ecc/
│   │   ├── __init__.py
│   │   ├── curve.py
│   │   ├── point.py
│   │   └── field_element.py
│   ├── ecdsa.py
│   ├── ed25519.py
│   ├── bls12_381.py
│   ├── merkle_tree.py
│   └── bloom_filter.py
├── vm/
│   ├── __init__.py
│   ├── opcode.py
│   ├── execution_engine.py
│   ├── execution_context.py
│   ├── evaluation_stack.py
│   ├── reference_counter.py
│   ├── slot.py
│   ├── script.py
│   ├── script_builder.py
│   ├── limits.py
│   ├── debugger.py
│   ├── types/
│   │   ├── __init__.py
│   │   ├── stack_item.py
│   │   ├── integer.py
│   │   ├── boolean.py
│   │   ├── byte_string.py
│   │   ├── buffer.py
│   │   ├── array.py
│   │   ├── struct.py
│   │   ├── map.py
│   │   ├── null.py
│   │   ├── pointer.py
│   │   └── interop_interface.py
│   └── instructions/
│       ├── __init__.py
│       ├── constants.py
│       ├── control_flow.py
│       ├── stack.py
│       ├── slot.py
│       ├── splice.py
│       ├── bitwise.py
│       ├── numeric.py
│       ├── comparison.py
│       ├── compound.py
│       └── types.py
├── smartcontract/
│   ├── __init__.py
│   ├── application_engine.py
│   ├── contract.py
│   ├── contract_state.py
│   ├── nef_file.py
│   ├── call_flags.py
│   ├── trigger.py
│   ├── storage_context.py
│   ├── storage_key.py
│   ├── storage_item.py
│   ├── key_builder.py
│   ├── find_options.py
│   ├── binary_serializer.py
│   ├── json_serializer.py
│   ├── interop_descriptor.py
│   ├── manifest/
│   │   ├── __init__.py
│   │   ├── contract_manifest.py
│   │   ├── contract_abi.py
│   │   ├── contract_method.py
│   │   ├── contract_event.py
│   │   ├── contract_group.py
│   │   └── contract_permission.py
│   ├── iterators/
│   │   ├── __init__.py
│   │   └── storage_iterator.py
│   └── syscalls/
│       ├── __init__.py
│       ├── runtime.py
│       ├── storage.py
│       ├── crypto.py
│       ├── contract.py
│       └── iterator.py
├── native/
│   ├── __init__.py
│   ├── native_contract.py
│   ├── fungible_token.py
│   ├── neo_token.py
│   ├── gas_token.py
│   ├── policy.py
│   ├── contract_management.py
│   ├── ledger.py
│   ├── oracle.py
│   ├── role_management.py
│   ├── crypto_lib.py
│   ├── std_lib.py
│   └── notary.py
├── network/
│   ├── __init__.py
│   └── payloads/
│       ├── __init__.py
│       ├── block.py
│       ├── header.py
│       ├── transaction.py
│       ├── witness.py
│       ├── signer.py
│       └── attributes/
│           ├── __init__.py
│           ├── transaction_attribute.py
│           ├── oracle_response.py
│           ├── not_valid_before.py
│           ├── conflicts.py
│           └── high_priority.py
├── persistence/
│   ├── __init__.py
│   ├── store.py
│   ├── snapshot.py
│   ├── data_cache.py
│   ├── store_cache.py
│   ├── cloned_cache.py
│   └── memory_store.py
└── ledger/
    ├── __init__.py
    ├── blockchain.py
    └── mempool.py
```

## Estimated Effort

- Phase 2: ~2000 lines
- Phase 3: ~500 lines
- Phase 4: ~1500 lines
- Phase 5: ~3000 lines
- Phase 6: ~4000 lines
- Phase 7: ~1500 lines
- Phase 8: ~1000 lines
- Phase 9: ~1500 lines
- Phase 10: ~1000 lines (optional)
- Phase 11: ~3000 lines (tests)

**Total: ~19,000+ lines of Python code**

## Version Tracking

Target: Neo N3 v3.9.1
Reference: https://github.com/neo-project/neo/releases/tag/v3.9.1
Neo-VM Reference: https://github.com/neo-project/neo-vm

## Next Steps

1. Complete VM opcodes (Phase 2)
2. Implement full cryptography (Phase 4)
3. Complete ApplicationEngine (Phase 5)
4. Implement all native contracts (Phase 6)
