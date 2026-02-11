# neo-rs Compatibility Helper Scripts

These scripts support local compatibility validation against a running `neo-rs` RPC node.

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

## Operational Notes

- Use these scripts for local investigation and release validation.
- For CI-level cross-client checks, use the built-in CLI tools:
  - `neo-compat`
  - `neo-multicompat`
  - `neo-coverage`
