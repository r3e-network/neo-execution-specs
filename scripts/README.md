# Compatibility Helper Scripts

These scripts support local compatibility validation and external endpoint drift checks.

## Prerequisites

- Start `neo-rs` with RPC enabled (default examples use `http://127.0.0.1:40332`).
- Install project dependencies: `pip install -e ".[all]"`.

## `neo_rs_vector_runner.py`

Run one vector file and write a normalized `neo-diff` JSON report.

```bash
python scripts/neo_rs_vector_runner.py tests/vectors/vm/control_flow.json \
  --rpc-url http://127.0.0.1:40332 \
  --output reports/neo-rs-batch/control_flow.json \
  --show-failures
```

Behavior:
- Returns non-zero for RPC/command errors or non-gas mismatches.
- Treats gas-only differences as pass by default (configurable via `--gas-tolerance`).

## `neo_rs_batch_diff.py`

Run all vector files in a directory and produce per-file reports plus a summary.

```bash
python scripts/neo_rs_batch_diff.py \
  --vectors-dir tests/vectors \
  --reports-dir reports/neo-rs-batch \
  --rpc-url http://127.0.0.1:40332 \
  --gas-tolerance 100000 \
  --delay-seconds 2
```

Behavior:
- Skips metadata-only files such as `checklist_coverage.json`.
- Returns non-zero for non-gas mismatches or execution errors.
- Use `--fail-on-gas-mismatch` for strict gas-delta failures.

## `neogo_endpoint_matrix.py`

Run a targeted C#/NeoGo endpoint matrix probe using expected delta vectors from
`docs/verification/neogo-0.116-known-deltas.txt`.

```bash
python3 scripts/neogo_endpoint_matrix.py \
  --output-dir reports/compat-endpoint-matrix \
  --prefix neogo-endpoint-matrix
```

Behavior:
- Builds a temporary probe vector set by selecting only expected delta vectors.
- Runs `neo-diff` pairwise (C# vs each NeoGo endpoint) for MainNet and TestNet.
- Verifies endpoint protocol expectations (network magic + useragent tokens) by default.
  NeoGo checks are matched by stable token prefix (`NEO-GO:`), not a pinned patch version.
- Writes per-endpoint reports and a summary JSON:
  - `reports/.../<prefix>-mainnet-*-csharp.json`
  - `reports/.../<prefix>-mainnet-*-neogo.json`
  - `reports/.../<prefix>-testnet-*-csharp.json`
  - `reports/.../<prefix>-testnet-*-neogo.json`
  - `reports/.../<prefix>-summary.json`
- Returns non-zero if any endpoint does not match expected deltas or protocol checks
  (unless `--allow-inconsistent` is provided).
- Use `--disable-protocol-checks` only for exploratory runs where network/useragent
  identity enforcement is intentionally relaxed.

## `check_native_surface_parity.py`

Validate local native-contract surface parity against a live Neo RPC endpoint.

```bash
python3 scripts/check_native_surface_parity.py \
  --rpc-url http://seed1.neo.org:10332 \
  --json-output reports/native-surface-mainnet.json
```

Behavior:
- Reads RPC `getversion`, `getblockcount`, and `getnativecontracts`.
- Generates local native contract states at the same block height context.
- Compares contract IDs/hashes, full method surface (name/params/types/offset/safe),
  event surface, supported standards, and `updatecounter`.
- Returns `0` on full parity, `1` on surface deltas, and `2` on RPC/config errors.

## Operational Notes

- Use these scripts for local investigation and release validation.
- For CI-level cross-client checks, use the built-in CLI tools:
  - `neo-compat`
  - `neo-multicompat`
  - `neo-coverage`
- For live-node `neo-diff` runs where committee-governed Policy values may drift,
  use `--allow-policy-governance-drift` to ignore only:
  `getFeePerByte`, `getExecFeeFactor`, and `getStoragePrice` value mismatches.
