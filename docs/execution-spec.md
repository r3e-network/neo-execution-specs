# Execution Specification (Neo v3.9.1 Profile)

This document defines the executable-spec profile implemented by `neo-execution-specs` for Neo N3 with protocol target `neo-project/neo@v3.9.1`.

It is the canonical high-level spec for:
- protocol configuration,
- state transition semantics,
- hardfork activation behavior,
- native contract surface rules,
- and conformance validation gates.

## 1. Conformance Target

- Reference protocol/runtime: `neo-project/neo` tag `v3.9.1`.
- Primary public compatibility endpoints:
  - MainNet C#: `http://seed1.neo.org:10332`
  - TestNet C#: `http://seed1t5.neo.org:20332`
- Compatibility model:
  - deterministic local execution via Python reference engine,
  - cross-check via `neo-diff` vectors,
  - native ABI/surface parity via live `getnativecontracts` comparison.

## 2. Protocol Profiles

### MainNet profile

- `network`: `860833102`
- `addressversion`: `53`
- `validatorscount`: `7`
- `msperblock`: `15000`
- `maxvaliduntilblockincrement`: `5760`
- `maxtransactionsperblock`: `512`
- hardfork heights:
  - `Aspidochelone`: `1730000`
  - `Basilisk`: `4120000`
  - `Cockatrice`: `5450000`
  - `Domovoi`: `5570000`
  - `Echidna`: `7300000`
  - `Faun`: `8800000`

### TestNet profile

- `network`: `894710606`
- `addressversion`: `53`
- `validatorscount`: `7`
- `msperblock`: `3000`
- `maxvaliduntilblockincrement`: `5760`
- `maxtransactionsperblock`: `5000`
- hardfork heights:
  - `Aspidochelone`: `210000`
  - `Basilisk`: `2680000`
  - `Cockatrice`: `3967000`
  - `Domovoi`: `4144000`
  - `Echidna`: `5870000`
  - `Faun`: `12960000`

Source of truth: `src/neo/protocol_settings.py`.

Global transaction envelope constant used by Neo N3:
- `maxtransactionsize`: `102400` bytes (`src/neo/network/payloads/transaction.py`).

## 3. Execution Model

### 3.1 VM execution core

- NeoVM execution is deterministic for a fixed script + context.
- Result state is one of:
  - `HALT`: successful execution with result stack,
  - `FAULT`: execution failed with exception.
- Core implementation:
  - `src/neo/vm/execution_engine.py`
  - `src/neo/smartcontract/application_engine.py`

### 3.2 Contract-call semantics

- `System.Contract.Call` and `CALLT`:
  - enforce call-flag subset checks,
  - enforce caller permission checks from manifest permissions,
  - resolve native vs deployed contracts by script hash,
  - reject inactive native contracts (hardfork-gated activation).

- `System.Contract.CallNative`:
  - resolves native method by active callnative syscall offset,
  - uses Neo v3.9.1 native stub shape: `PUSH0 + SYSCALL + RET` (7 bytes),
  - validates native version selector (`0` required),
  - enforces required native call flags.

### 3.3 Hardfork activation and method/event gating

- Hardfork checks are evaluated against `persisting_block.index`.
- Methods/events can be:
  - active from a hardfork (`active_in`),
  - deprecated at a hardfork (`deprecated_in`).
- Contracts can be activation-gated at contract level.
- Native contract dynamic manifests are generated from active methods/events in context.

### 3.4 Native contract lifecycle and update counters

- Native `ContractState.update_counter` follows hardfork reinitialization semantics:
  - contract creation activation height,
  - plus hardforks referenced by contract/method/event activations/deprecations,
  - counted up to current block index.

This mirrors v3.9.1 behavior for all 11 native contracts.

### 3.5 `neo-t8n` transition profile

`neo-t8n` is the execution-spec transition harness for deterministic script execution across a provided pre-state.

Execution behavior:
- each input transaction script executes through `ApplicationEngine` with `TriggerType.APPLICATION`,
- block context is bound from `env` (`currentBlockNumber`, `timestamp`, `primaryIndex`, `nonce`),
- network magic from `env.network` is forwarded into runtime context (`System.Runtime.GetNetwork`),
- protocol settings use mainnet/testnet v3.9.1 profiles when network matches known magic values; unknown networks keep v3.9.1 defaults with the provided magic,
- transaction pre-validation checks include:
  - transaction-list block bound (`txs` length must not exceed profile `max_transactions_per_block`),
  - script hex decoding,
  - non-empty transaction script requirement,
  - max unsigned transaction size bound (`<= 102400` bytes), including envelope + signers + script var-size encoding,
    with unsigned serialization modeled as `version, nonce, systemFee, networkFee, validUntilBlock, signers, attributes(varint=0), script`,
  - non-negative `systemFee` / `networkFee` and int64 bounds,
  - `nonce` uint32 bounds,
  - `validUntilBlock` uint32 bounds,
  - `validUntilBlock` expiry (`<= currentBlockNumber`) and max increment bounds,
  - signer count bounds (at most 16 signers),
  - duplicate signer-account rejection,
  - signer `WitnessScope` flag validation (including `GLOBAL` non-combinability),
  - signer account and allowed-contract hash widths,
  - signer allowed-contract/group list bounds (at most 16 entries each),
  - signer allowed-contract/group scope consistency (`allowedContracts` requires `CUSTOM_CONTRACTS`; `allowedGroups` requires `CUSTOM_GROUPS`),
  - signer allowed-group public-key width checks (33-byte compressed points),
  - signer witness-rule shape validation (required `action` + `condition`),
  - signer witness-rule scope consistency (`rules` require `WITNESS_RULES` scope),
  - witness-rule limits aligned with Neo v3.9.1 payload bounds:
    - at most 16 rules per signer,
    - witness-condition nesting depth `<= 2`,
    - `AND`/`OR` witness-condition subitems `<= 16`,
    - hash/group witness-condition field checks (`20`-byte hash, `33`-byte compressed ECPoint group).

Input error handling:
- malformed/expired transactions produce a `FAULT` receipt with exception text,
- malformed tx object shapes/field types (for example missing `script`, non-array `signers`, non-integer numeric fields) are surfaced as per-tx `FAULT` receipts,
- transition execution continues for later transactions in the same run (no whole-run abort).
- tx-list block-bound overflow is treated as:
  - permissive mode: per-tx `FAULT` receipts and no tx execution,
  - strict mode: fail-fast error.
- optional strict mode switches to fail-fast behavior (first validation/execution error aborts the run).

Receipt behavior:
- `vmState`: `HALT` or `FAULT`,
- `gasConsumed`: engine gas consumed (opcode + syscall metering),
- `stack`: projected top-first VM result stack (`type` + `value`),
- `notifications`: projected runtime notifications (`contract`, `eventName`, `state`),
- `txHash`: deterministic receipt identifier produced by `neo-t8n` materialization (not a canonical network transaction hash),
- `exception`: included for faulted executions.

Post-state alloc behavior:
- output remains in the same account-oriented schema as input (`neoBalance`, `gasBalance`, `storage`, optional metadata),
- post-state is reconstructed from committed snapshot state, not raw snapshot key dumps,
- only the `neo-t8n` alloc namespace is projected (balance keys + account storage keys used by `neo-t8n`).

## 4. Native Contract Profile (v3.9.1)

| Contract | ID | Hash | Activation |
|---|---:|---|---|
| ContractManagement | -1 | `0xfffdc93764dbaddd97c48f252a53ea4643faa3fd` | Genesis |
| StdLib | -2 | `0xacce6fd80d44e1796aa0c2c625e9e4e0ce39efc0` | Genesis |
| CryptoLib | -3 | `0x726cb6e0cd8628a1350a611384688911ab75f51b` | Genesis |
| LedgerContract | -4 | `0xda65b600f7124ce6c79950c1772a36403104f2be` | Genesis |
| NeoToken | -5 | `0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5` | Genesis |
| GasToken | -6 | `0xd2a4cff31913016155e38e474a2c06d08be276cf` | Genesis |
| PolicyContract | -7 | `0xcc5e4edd9f5f8dba8bb65734541df7a1c081c67b` | Genesis |
| RoleManagement | -8 | `0x49cf4e5378ffcd4dec034fd98a174c5491e395e2` | Genesis |
| OracleContract | -9 | `0xfe924b7cfe89ddd271abaf7210a80a7e11178758` | Genesis |
| Notary | -10 | `0xc1e14f19c3e60d0b9244d06dd7ba9b113135ec3b` | Echidna |
| Treasury | -11 | `0x156326f25b1b5d839a4d326aeaa75383c9563ac1` | Faun |

## 5. Storage and State Rules

- Native storage keys are prefixed by contract id and native-specific key prefixes.
- Contract storage key lookup uses Neo N3 key layout (`contract_id` + user key).
- State transition snapshots use persistence cache layers (`MemorySnapshot`, cloned caches, tracked changes).

Primary modules:
- `src/neo/persistence/*`
- `src/neo/smartcontract/storage/*`
- `src/neo/native/native_contract.py`

## 6. Conformance Gates

Minimum release gates for this profile:

1. Coverage matrix gate
   - `neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md --coverage-manifest tests/vectors/checklist_coverage.json --vectors-root tests/vectors/`
2. Full test gate
   - `PYTHONPATH=src pytest -q`
3. Vector validation
   - `cd tests/vectors && python3 validate.py`
4. C# compatibility vectors
   - `neo-diff --vectors tests/vectors --csharp-rpc <v3.9.1-rpc>`
5. Live native surface parity
   - `python3 scripts/check_native_surface_parity.py --rpc-url <v3.9.1-rpc>`

## 7. Scope Boundaries

This repository is an executable specification, not a high-performance full node implementation.

Goals:
- clarity, determinism, and protocol explainability,
- strong conformance signals against v3.9.1 behavior,
- reproducible vector-driven validation.

Non-goals:
- P2P production operations tuning,
- throughput-optimized execution paths.
