# Neo v3.9.1 Deep Compatibility Review

Date: 2026-02-07
Repository: `neo-execution-specs`
Target: Neo protocol/runtime compatibility with `neo-project/neo` tag `v3.9.1`

## Scope and Method

This review verified compatibility through:

1. **Reference source diffing** against `neo-project/neo@v3.9.1`.
2. **Live RPC protocol validation** against Neo v3.9.1 nodes (`getversion`).
3. **Behavioral regression tests** (unit tests + vector validation + cross-implementation `neo-diff`).
4. **Compatibility lock tests** to prevent future drift.

## Fixed In This Review

### 1) Syscall metadata drift (critical)

Aligned Python syscall registration with Neo v3.9.1 `InteropDescriptor` values:

- Corrected prices for Runtime/Storage/Contract syscalls.
- Corrected required call flags for gated syscalls.
- Added missing hardfork-gated syscalls:
  - `System.Storage.Local.Get`
  - `System.Storage.Local.Find`
  - `System.Storage.Local.Put`
  - `System.Storage.Local.Delete`
- Added hardfork-aware syscall activation checks.
- Added runtime call-flag enforcement in syscall invocation.

Files:
- `src/neo/smartcontract/application_engine.py`
- `src/neo/smartcontract/interop_service.py`

### 2) Testnet protocol mismatch (critical)

From live Neo v3.9.1 testnet RPC (`seed1t5.neo.org:20332`),
`msperblock` is `3000`.

Updated:
- `ProtocolSettings.testnet().milliseconds_per_block` from `15000` to `3000`.

File:
- `src/neo/protocol_settings.py`

## Added Compatibility Regression Tests

- `tests/smartcontract/test_syscall_compatibility_v391.py`
  - Locks full syscall table (price, flags, hardfork gate) to Neo v3.9.1.
  - Verifies required call-flag enforcement.
  - Verifies hardfork gating for `System.Storage.Local.*`.

- `tests/test_protocol_settings.py`
  - Added testnet v3.9.1 default assertions (network, timing, hardfork heights, seed list).

## Validation Evidence

### Full unit test suite

- Command: `PYTHONPATH=src .venv/bin/pytest tests/ -q`
- Result: `1075 passed, 1 warning`

### Vector validation

- Command: `cd tests/vectors && python3 validate.py`
- Result: `125 passed, 0 failed`

### Cross-implementation diff (Python vs Neo v3.9.1 RPC)

- Command: `neo-diff --vectors tests/vectors/ --csharp-rpc <Neo v3.9.1 endpoint>`
- Result summary:
  - `total=147`
  - `passed=147`
  - `failed=0`
  - `errors=0`
  - `pass_rate=100.00%`

## Live RPC Protocol Spot-Checks

### Mainnet (`seed1.neo.org:10332`)

Confirmed against live `getversion`:
- `network=860833102`
- `addressversion=53`
- `validatorscount=7`
- `msperblock=15000`
- `maxvaliduntilblockincrement=5760`
- hardfork heights up to `Faun=8800000`

### Testnet (`seed1t5.neo.org:20332`)

Confirmed against live `getversion`:
- `network=894710606`
- `addressversion=53`
- `validatorscount=7`
- `msperblock=3000` ✅ (fixed in this review)
- `maxvaliduntilblockincrement=5760`
- hardfork heights up to `Faun=12960000`

## Conclusion

The reviewed and covered protocol/runtime surface is now aligned with Neo v3.9.1 and validated locally with passing tests and cross-node diff checks.

For the covered execution vectors and syscall metadata, compatibility is verified.
