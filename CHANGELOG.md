# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `Treasury` native contract integration and dedicated coverage tests (`tests/native/test_treasury_contract.py`).
- Added native v3.9.1 method-surface lock test (`tests/native/test_native_method_surface_v391.py`) to prevent ABI drift.
- Added native v3.9.1 identity lock checks for all native contract IDs/hashes (`tests/native/test_native_method_surface_v391.py`).
- Added NeoGo endpoint-matrix automation script (`scripts/neogo_endpoint_matrix.py`) with unit tests (`tests/tools/test_neogo_endpoint_matrix_script.py`).
- Added scheduled/manual endpoint drift workflow (`.github/workflows/neogo-endpoint-matrix.yml`) with artifact + summary publishing.
- Added dated compatibility verification evidence for NeoGo 0.116 (`docs/verification/neogo-0.116-validation-2026-02-16.md`).

### Changed
- Updated Policy native defaults to match Neo v3.9.1 live baseline (`FeePerByte=20`, `ExecFeeFactor=1`, `StoragePrice=1000`).
- Tightened Policy protocol invariants to Neo v3.9.1 limits (`MillisecondsPerBlock<=30000`, `MaxValidUntilBlockIncrement<=86400`, `MaxTraceableBlocks<=2102400`) and enforced cross-parameter constraints.
- Corrected Policy whitelist-fee storage prefix to `16` (Neo v3.9.1).
- Aligned Policy whitelist fee handling with Neo v3.9.1 contract/method validation by resolving ABI method offsets from ContractManagement state before set/remove.
- Implemented Policy `recoverFund` protocol flow (1-year blocked-account timelock, NEP-17 contract validation, native-call transfer context, Treasury transfer, recovered-fund notification) and added targeted regression coverage.
- Aligned Policy method metadata to Neo v3.9.1 `CallFlags` expectations for notify-capable methods and added metadata lock tests.
- Aligned Policy `blockAccount` with Faun-era vote handling by clearing existing NEO votes (`NeoToken.vote_internal(..., None)`) when an account is blocked.
- Aligned active Neo v3.9.1 native method metadata for `NeoToken` and `ContractManagement` (`CallFlags`/CPU fee), including notify-gated governance methods and `isContract`/`getCommitteeAddress` fee corrections.
- Added `recoverFund` regression coverage for deployed NEP-17 contracts when `transfer` returns `false`, locking failure-path behavior.
- Added Policy hardfork-aware behavior checks for Echidna/Faun-gated methods and aligned pre-Faun `blockAccount` semantics (no vote clearing, empty blocked entry value).
- Added StdLib hardfork-aware handling for Echidna/Faun methods (`base64UrlEncode`/`base64UrlDecode`/`hexEncode`/`hexDecode`) with explicit activation checks and regression tests.
- Hardened `LedgerContract` persistence/query behavior by storing decodable transaction payloads, supporting real `Block` serialization paths during persistence, and implementing indexed transaction retrieval from persisted block bytes (`getTransactionFromBlock`).
- Hardened native method dispatch in `ApplicationEngine` by adding stack argument marshalling with signature-based context injection (`engine`/`snapshot`), typed conversion (`UInt160`/`UInt256`/enums/collections), and compatibility support for `(value, context=None)` handlers.
- Added end-to-end `System.Contract.CallNative` integration coverage across native signature classes (`snapshot`, `engine`, `(value, context=None)`) and explicit call-flag rejection behavior.
- Added hardfork-boundary `System.Contract.CallNative` regression coverage for Echidna/Faun-gated native methods (`ContractManagement.isContract`, `PolicyContract.getExecPicoFeeFactor`, `StdLib.base64UrlEncode`).
- Expanded `System.Contract.CallNative` hardfork-boundary coverage for additional Echidna/Faun-gated methods (`PolicyContract.getMillisecondsPerBlock`, `getMaxValidUntilBlockIncrement`, `getMaxTraceableBlocks`, `getBlockedAccounts`, `getWhitelistFeeContracts`, `StdLib.hexEncode`, `StdLib.hexDecode`).
- Added `System.Contract.CallNative` regression coverage for native return-type projection into VM stack types (Python `list` -> VM `Array`, `dict` -> VM `Map`, `UInt160/UInt256` -> `ByteString`).
- Added integration coverage for native invocations through `System.Contract.Call` and `CALLT` (`tests/smartcontract/test_contract_call_native_integration.py`), including argument-order and caller-permission enforcement behavior.
- Updated StdLib radix behavior to match live semantics for hex signedness/formatting (`itoa`/`atoi`).
- Expanded native contract method coverage (ContractManagement, NeoToken, Policy, Treasury) and aligned documentation to 11 native contracts.
- Hardened `neo-diff` native execution path to use real native contract method dispatch in compatibility runs.
- Hardened BLS fallback behavior to fail closed when optional pairing dependencies are unavailable.
- Refreshed production/testing/API docs to reflect current compatibility gates, known NeoGo 5-vector deltas, and endpoint matrix automation.
- Hardened `ApplicationEngine` native return marshalling to project structured values to VM stack items while preserving iterator-like results as interop objects (prevents unintended iterator-to-bytes coercion).
- Hardened `ApplicationEngine` native contract resolution and call-path behavior by:
  - resolving native contracts through global native registries in `System.Contract.Call` / `CALLT` flows;
  - dispatching native methods directly in `_call_contract_internal` with required call-flag and gas checks;
  - enforcing caller-permission checks for native dynamic calls.
- Hardened `System.Contract.CallNative` offset dispatch to use hardfork-aware active native method maps, and annotated Echidna/Faun-gated native methods with activation metadata so pre-/post-fork method availability and offsets follow active method sets.
- Aligned `System.Contract.CallNative` native-script semantics with Neo v3.9.1 by modeling 7-byte stubs (`PUSH0 + SYSCALL + RET`) at SYSCALL offsets and rejecting non-zero native versions.
- Enforced hardfork activation checks for native method-name dispatch in both `System.Contract.Call` and `CALLT`, so inactive gated methods are denied before invocation.
- Hardened `CALLT` dispatch to enforce the same method-permission gate as `System.Contract.Call`.
- Aligned `Treasury` native method metadata and behavior to Neo v3.9.1 (`CallFlags`/CPU fees, committee-gated `verify`) and added metadata lock coverage.

## [0.1.2] - 2026-02-12

### Added

- Added `docs/production-readiness.md` with release-grade validation criteria and operational gates.
- Added `tests/tools/test_release_metadata.py` to enforce version/changelog consistency locally.
- Added `scripts/check_release_metadata.py` as a reusable metadata validation CLI used by local checks and CI.

### Changed

- Hardened local neo-rs helper scripts (`scripts/neo_rs_vector_runner.py`, `scripts/neo_rs_batch_diff.py`) with robust CLI behavior and deterministic exit status.
- Strengthened CI with packaging/entrypoint smoke checks in `.github/workflows/test.yml`.
- Hardened release workflow with tag/version/changelog consistency checks in `.github/workflows/release.yml` and fixed tag parsing to use runtime environment values correctly.
- Updated test workflow packaging lane to run metadata validation and clean build artifacts before building distributions.
- Updated contribution guidance and script/testing docs for production-oriented workflows.
- Replaced static README test count badge with CI workflow status badge and corrected repository clone URL.
- Hardened `check_release_metadata.py` to validate real calendar dates in changelog headings, support single- or double-quoted `__version__`, and surface file-read errors cleanly.
- Aligned README, contribution guide, and production checklist packaging commands with CI (`build`/`twine` install + clean `dist`/`build`).
- Enforced semantic version format (`X.Y.Z`) for `pyproject.toml` release metadata validation via `scripts/check_release_metadata.py`.
- Hardened GitHub Actions workflows with explicit least-privilege `permissions` and `concurrency` controls across test, release, diff, and vector workflows.
- Refreshed `docs/testing.md` CI section to match live workflow topology and reduce documentation drift.
- Added `scripts/check_mypy_regressions.py` and `scripts/mypy-error-baseline.txt` to enforce a no-regression mypy baseline in CI while existing typing debt is reduced.
- Updated test workflow and contributor/readme/production docs to include the mypy baseline gate command.
- Eliminated all remaining mypy errors across `src/neo` and set `scripts/mypy-error-baseline.txt` to `0` for strict type enforcement in CI.

## [0.1.1] - 2026-02-11

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

- **neo-rs compatibility helper scripts**
  - Added `scripts/neo_rs_vector_runner.py` and `scripts/neo_rs_batch_diff.py` to support direct neo-rs vector execution and batch reporting.

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
