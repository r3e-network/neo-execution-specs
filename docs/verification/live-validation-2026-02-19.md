# Live Compatibility Validation Snapshot (2026-02-19)

This note captures a fresh live check of `neo-execution-specs` against public Neo N3 endpoints after protocol-surface and tooling updates in this repository.

## Endpoint versions checked

- MainNet C#: `http://seed1.neo.org:10332` -> `/Neo:3.9.1/`
- TestNet C#: `http://seed1t5.neo.org:20332` -> `/Neo:3.9.1/`
- MainNet NeoGo: `http://rpc3.n3.nspcc.ru:10332` -> `/NEO-GO:0.117.0/`
- TestNet NeoGo: `http://rpc.t5.n3.nspcc.ru:20332` -> `/NEO-GO:0.117.0/`

## Key results

1. C# strict vector run on live MainNet endpoint now reports `402/405`.
2. All 3 failures are `PolicyContract` value vectors:
   - `Policy_getFeePerByte`
   - `Policy_getExecFeeFactor`
   - `Policy_getStoragePrice`
3. Live policy values on both MainNet and TestNet are currently:
   - `getFeePerByte` => `20`
   - `getExecFeeFactor` => `1`
   - `getStoragePrice` => `1000`
4. The repository baseline vectors still encode Neo v3.9.1 native defaults:
   - `1000`, `30`, `100000`
5. Live C# vs NeoGo compatibility on MainNet:
   - strict mode: C# `402/405`, NeoGo `397/405`, cross-client deltas `5` (TRY/ENDTRY family)
   - ignore-list mode (`docs/verification/neogo-0.116-known-deltas.txt`): C# `397/400`, NeoGo `397/400`, cross-client deltas `0`
6. Live C# vs NeoGo compatibility on TestNet:
   - strict mode rerun: C# `402/405`, NeoGo `397/405`, cross-client deltas `5` (same TRY/ENDTRY family)
   - ignore-list mode (`docs/verification/neogo-0.116-known-deltas.txt`): C# `397/400`, NeoGo `397/400`, cross-client deltas `0`
7. One TestNet strict run produced an additional transient `ASSERTMSG_false_fault` delta (`6` deltas total), but:
   - a full strict rerun returned to the canonical `5` deltas, and
   - 3 direct `ASSERTMSG_false_fault` NeoGo TestNet probes all passed.
8. Native contract surface parity against live MainNet and TestNet C# reports full parity (`11` contracts compared, all mismatch counters `0` on both networks).
9. NeoGo endpoint matrix still reproduces the same 5 known TRY/ENDTRY deltas across all public endpoints, now on `0.117.0`.
10. Local `neo-rs` validation run (latest pulled `neo-rs` commit `4cf994c2`) reports full vector pass:
    - `neo-diff` (mainnet vectors): `405/405`
    - `neo-diff` strict rerun: `405/405`
11. MainNet triplet comparison (`C#` vs `NeoGo` vs local `neo-rs`) with ignore list
    (`docs/verification/neogo-0.116-known-deltas.txt`) reports:
    - `csharp_vs_neogo`: `0`
    - `csharp_vs_neo_rs`: `3`
    - `neo_rs_vs_neogo`: `3`
    - all 3 deltas are policy vectors: `Policy_getExecFeeFactor`, `Policy_getFeePerByte`,
      `Policy_getStoragePrice`

## Artifacts

- `reports/compat-live-2026-02-19/compat-mainnet-strict-2026-02-19-csharp.json`
- `reports/compat-live-2026-02-19/compat-mainnet-strict-2026-02-19-neogo.json`
- `reports/compat-live-2026-02-19/compat-mainnet-ignore-2026-02-19-csharp.json`
- `reports/compat-live-2026-02-19/compat-mainnet-ignore-2026-02-19-neogo.json`
- `reports/native-surface-mainnet-2026-02-19.json`
- `reports/compat-live-2026-02-19/compat-testnet-strict-2026-02-19-csharp.json`
- `reports/compat-live-2026-02-19/compat-testnet-strict-2026-02-19-neogo.json`
- `reports/compat-live-2026-02-19/compat-testnet-strict-rerun-2026-02-19-csharp.json`
- `reports/compat-live-2026-02-19/compat-testnet-strict-rerun-2026-02-19-neogo.json`
- `reports/compat-live-2026-02-19/compat-testnet-ignore-2026-02-19-csharp.json`
- `reports/compat-live-2026-02-19/compat-testnet-ignore-2026-02-19-neogo.json`
- `reports/compat-live-2026-02-19/neogo-testnet-controlflow-1.json`
- `reports/compat-live-2026-02-19/neogo-testnet-controlflow-2.json`
- `reports/compat-live-2026-02-19/neogo-testnet-controlflow-3.json`
- `reports/native-surface-testnet-2026-02-19.json`
- `reports/policy-csharp-live-2026-02-18.json`
- `reports/policy-neogo-live-2026-02-18.json`
- `reports/compat-endpoint-matrix-live-2026-02-18/neogo-endpoint-matrix-live-2026-02-18-summary.json`
- `reports/neo-rs-live-2026-02-19/neo-rs-mainnet-vectors.json`
- `reports/neo-rs-live-2026-02-19/neo-rs-mainnet-vectors-strict.json`
- `reports/compat-live-2026-02-19/compat-triplet-mainnet-neo-rs-2026-02-19-csharp.json`
- `reports/compat-live-2026-02-19/compat-triplet-mainnet-neo-rs-2026-02-19-neogo.json`
- `reports/compat-live-2026-02-19/compat-triplet-mainnet-neo-rs-2026-02-19-neo_rs.json`

## Notes

- This repo’s policy constants match `neo-project/neo@v3.9.1` defaults and unit baselines.
- Live public nodes can differ from defaults due to committee/governance updates.
- Endpoint matrix tooling now matches NeoGo by stable token prefix (`NEO-GO:`), not a pinned patch version.
- The local `neo-rs` run used `neo_mainnet_multicompat.toml` and a fresh storage path
  (`./data/mainnet-v072-validation-tty`) to match `neo-rs` `0.7.2` storage format.
