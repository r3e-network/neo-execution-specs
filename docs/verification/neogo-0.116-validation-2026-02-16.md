# NeoGo 0.116 Compatibility Verification Snapshot (2026-02-16)

This note captures a point-in-time live compatibility verification for `neo-execution-specs` against Neo N3 C# 3.9.1 and NeoGo 0.116.0, with tri-client probes including local `neo-rs` endpoints.

## Verification metadata

- Date checked (UTC): `2026-02-16 03:47:03Z`
- Vectors: `tests/vectors/` (405 vectors loaded; 6 skipped by unsupported/missing-script guards)
- Report directory: `reports/compat-2026-02-15/`

## Release status

- NeoGo latest GitHub release: `v0.116.0`
- Published at: `2026-01-21T15:00:52Z`
- Release URL: https://github.com/nspcc-dev/neo-go/releases/tag/v0.116.0

## Endpoint versions checked

MainNet:
- `http://seed1.neo.org:10332` -> network `860833102`, useragent `/Neo:3.9.1/`
- `http://rpc3.n3.nspcc.ru:10332` -> network `860833102`, useragent `/NEO-GO:0.116.0/`

TestNet:
- `http://seed1t5.neo.org:20332` -> network `894710606`, useragent `/Neo:3.9.1/`
- `http://rpc.t5.n3.nspcc.ru:20332` -> network `894710606`, useragent `/NEO-GO:0.116.0/`

Local `neo-rs` probe:
- `http://127.0.0.1:40332` -> connection refused (`curl: (7)`)
- `http://127.0.0.1:41332` -> connection refused (`curl: (7)`)

## Public NeoGo endpoint matrix (delta-5 probe)

A targeted probe was run against all published NSPCC NeoGo endpoints using only the 5 known delta vectors:

- `STATE_exec_try_l_no_exception`
- `TRY_no_exception`
- `TRY_with_throw_catch`
- `TRY_L_no_exception`
- `TRY_finally_no_exception`

Endpoints checked:

- MainNet: `rpc1..rpc7.n3.nspcc.ru:10332` (each against `seed1.neo.org:10332`)
- TestNet: `rpc.t5.n3.nspcc.ru:20332` (against `seed1t5.neo.org:20332`)

Result:

- All 8 NeoGo endpoints reproduced the same 5/5 deltas (`Vector deltas: 5`).
- For every endpoint probe: C# `5/5 passed`, NeoGo `0/5 passed`.
- Automated matrix helper (`scripts/neogo_endpoint_matrix.py`) reported
  `all_matches_expected: true`, `all_vector_matches_expected: true`,
  `all_protocol_matches_expected: true`, and `had_errors: false`.

Artifacts:

- `reports/compat-2026-02-16-endpoints/` (`mainnet-rpc1-delta5-*` ... `mainnet-rpc7-delta5-*`, `testnet-rpct5-delta5-*`)
- `reports/compat-2026-02-16-endpoints-script/neogo-0.116-endpoint-matrix-summary.json`
- `reports/compat-2026-02-16-endpoints-script/neogo-0.116-endpoint-matrix-*.json`

## `neo-compat` strict results

MainNet (`mainnet-strict-*`):
- C#: `405/405 passed`
- NeoGo: `400/405 passed` (`5` deltas)

TestNet (`testnet-strict-*`):
- C#: `405/405 passed`
- NeoGo: `400/405 passed` (`5` deltas)

Strict NeoGo delta vectors (same on MainNet/TestNet):
- `STATE_exec_try_l_no_exception`
- `TRY_no_exception`
- `TRY_with_throw_catch`
- `TRY_L_no_exception`
- `TRY_finally_no_exception`

Artifacts:
- `reports/compat-2026-02-15/mainnet-strict-csharp.json`
- `reports/compat-2026-02-15/mainnet-strict-neogo.json`
- `reports/compat-2026-02-15/testnet-strict-csharp.json`
- `reports/compat-2026-02-15/testnet-strict-neogo.json`

## Known-delta ignore verification

Initial ignore file (`docs/verification/neogo-0.116-known-deltas.txt`) contained 4 TRY vectors. Re-run showed:
- `Ignored vectors: 4`
- `Vector deltas: 1`
- Remaining mismatch: `STATE_exec_try_l_no_exception`

The ignore list was then updated to include `STATE_exec_try_l_no_exception` (now 5 vectors total), and re-run produced:
- MainNet: `C# summary total=400 passed=400`, `NeoGo summary total=400 passed=400`, `Vector deltas: 0`, `Ignored vectors: 5`
- TestNet: `C# summary total=400 passed=400`, `NeoGo summary total=400 passed=400`, `Vector deltas: 0`, `Ignored vectors: 5`

Artifacts:
- `reports/compat-2026-02-15/mainnet-ignore-csharp.json`
- `reports/compat-2026-02-15/mainnet-ignore-neogo.json`
- `reports/compat-2026-02-15/testnet-ignore-csharp.json`
- `reports/compat-2026-02-15/testnet-ignore-neogo.json`
- `reports/compat-2026-02-15/mainnet-ignore5-csharp.json`
- `reports/compat-2026-02-15/mainnet-ignore5-neogo.json`
- `reports/compat-2026-02-15/testnet-ignore5-csharp.json`
- `reports/compat-2026-02-15/testnet-ignore5-neogo.json`

## `neo-multicompat` strict triplet results

MainNet (`mainnet-tri-strict-*`):
- csharp: `405/405 passed`
- neogo: `400/405 passed`
- neo_rs: `0/405 passed` (`405/405 failed`, endpoint results as `ERROR`)
- Pairwise vector deltas:
  - `csharp_vs_neogo: 5`
  - `csharp_vs_neo_rs: 405`
  - `neo_rs_vs_neogo: 405`

TestNet (`testnet-tri-strict-*`):
- csharp: `405/405 passed`
- neogo: `400/405 passed`
- neo_rs: `0/405 passed` (`405/405 failed`, endpoint results as `ERROR`)
- Pairwise vector deltas:
  - `csharp_vs_neogo: 5`
  - `csharp_vs_neo_rs: 405`
  - `neo_rs_vs_neogo: 405`

Artifacts:
- `reports/compat-2026-02-15/mainnet-tri-strict-csharp.json`
- `reports/compat-2026-02-15/mainnet-tri-strict-neogo.json`
- `reports/compat-2026-02-15/mainnet-tri-strict-neo_rs.json`
- `reports/compat-2026-02-15/testnet-tri-strict-csharp.json`
- `reports/compat-2026-02-15/testnet-tri-strict-neogo.json`
- `reports/compat-2026-02-15/testnet-tri-strict-neo_rs.json`

## Commands executed

```bash
# strict two-client checks
PYTHONPATH=src neo-compat --vectors tests/vectors/ --csharp-rpc http://seed1.neo.org:10332 --neogo-rpc http://rpc3.n3.nspcc.ru:10332 --output-dir reports/compat-2026-02-15 --prefix mainnet-strict
PYTHONPATH=src neo-compat --vectors tests/vectors/ --csharp-rpc http://seed1t5.neo.org:20332 --neogo-rpc http://rpc.t5.n3.nspcc.ru:20332 --output-dir reports/compat-2026-02-15 --prefix testnet-strict

# automated endpoint matrix helper (expected deltas file driven)
python3 scripts/neogo_endpoint_matrix.py \
  --output-dir reports/compat-2026-02-16-endpoints-script \
  --prefix neogo-0.116-endpoint-matrix

# targeted endpoint matrix (5-vector NeoGo delta probe)
probe_dir=$(mktemp -d)
jq '{name,description,category,version,vectors: [.vectors[] | select(.name=="TRY_no_exception" or .name=="TRY_with_throw_catch" or .name=="TRY_L_no_exception" or .name=="TRY_finally_no_exception")]}' tests/vectors/vm/control_flow_deep.json > "$probe_dir/control_flow_deep.json"
jq '{name,description,category,version,vectors: [.vectors[] | select(.name=="STATE_exec_try_l_no_exception")]}' tests/vectors/state/executable_state_deep.json > "$probe_dir/executable_state_deep.json"
for i in 1 2 3 4 5 6 7; do
  PYTHONPATH=src neo-compat --vectors "$probe_dir" --csharp-rpc http://seed1.neo.org:10332 --neogo-rpc "http://rpc${i}.n3.nspcc.ru:10332" --output-dir reports/compat-2026-02-16-endpoints --prefix "mainnet-rpc${i}-delta5"
done
PYTHONPATH=src neo-compat --vectors "$probe_dir" --csharp-rpc http://seed1t5.neo.org:20332 --neogo-rpc http://rpc.t5.n3.nspcc.ru:20332 --output-dir reports/compat-2026-02-16-endpoints --prefix testnet-rpct5-delta5

# ignore-file checks (4-vector file, then updated 5-vector file)
PYTHONPATH=src neo-compat --vectors tests/vectors/ --csharp-rpc http://seed1.neo.org:10332 --neogo-rpc http://rpc3.n3.nspcc.ru:10332 --ignore-vectors-file docs/verification/neogo-0.116-known-deltas.txt --output-dir reports/compat-2026-02-15 --prefix mainnet-ignore
PYTHONPATH=src neo-compat --vectors tests/vectors/ --csharp-rpc http://seed1t5.neo.org:20332 --neogo-rpc http://rpc.t5.n3.nspcc.ru:20332 --ignore-vectors-file docs/verification/neogo-0.116-known-deltas.txt --output-dir reports/compat-2026-02-15 --prefix testnet-ignore
PYTHONPATH=src neo-compat --vectors tests/vectors/ --csharp-rpc http://seed1.neo.org:10332 --neogo-rpc http://rpc3.n3.nspcc.ru:10332 --ignore-vectors-file docs/verification/neogo-0.116-known-deltas.txt --output-dir reports/compat-2026-02-15 --prefix mainnet-ignore5
PYTHONPATH=src neo-compat --vectors tests/vectors/ --csharp-rpc http://seed1t5.neo.org:20332 --neogo-rpc http://rpc.t5.n3.nspcc.ru:20332 --ignore-vectors-file docs/verification/neogo-0.116-known-deltas.txt --output-dir reports/compat-2026-02-15 --prefix testnet-ignore5

# strict triplet checks
PYTHONPATH=src neo-multicompat --vectors tests/vectors/ --csharp-rpc http://seed1.neo.org:10332 --neogo-rpc http://rpc3.n3.nspcc.ru:10332 --neo-rs-rpc http://127.0.0.1:40332 --output-dir reports/compat-2026-02-15 --prefix mainnet-tri-strict
PYTHONPATH=src neo-multicompat --vectors tests/vectors/ --csharp-rpc http://seed1t5.neo.org:20332 --neogo-rpc http://rpc.t5.n3.nspcc.ru:20332 --neo-rs-rpc http://127.0.0.1:41332 --output-dir reports/compat-2026-02-15 --prefix testnet-tri-strict
```

## Conclusion

- `neo-execution-specs` remains aligned with Neo C# 3.9.1 for this vector suite.
- NeoGo 0.116.0 shows a stable 5-vector TRY/ENDTRY control-flow delta on both MainNet and TestNet.
- The known-delta file is now complete for this reproducible NeoGo delta set in current verification (`5` vectors).
- Local `neo-rs` endpoints are not serving compatible RPC in this environment (connection refused by direct probe; full-vector `ERROR` behavior in triplet runs), so tri-client parity cannot be claimed until a working Neo N3 `neo-rs` node is available.
