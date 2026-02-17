# neo-t8n Envelope Validation Hardening Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align `neo-t8n` transaction-envelope validation more closely with Neo v3.9.1 expectations while preserving permissive execution mode ergonomics.

**Architecture:** Extend `T8N._validate_tx` with fee, `validUntilBlock`, signer-duplication, and witness-scope checks. Keep permissive default as per-tx `FAULT` receipts and strict mode as fail-fast. Lock behavior with focused tool tests and runtime signer/witness checks.

**Tech Stack:** Python 3.11+, `pytest`, `ApplicationEngine`, `WitnessScope`.

### Task 1: Add failing validation tests

**Files:**
- Modify: `tests/tools/test_t8n.py`

**Step 1: Add RED tests for missing envelope checks**
- Add tests for:
  - `validUntilBlock <= currentBlockNumber` faulting,
  - `validUntilBlock` max-increment overflow faulting,
  - negative fee rejection,
  - duplicate signer rejection,
  - invalid/malformed witness scope rejection,
  - invalid allowed-group width rejection.

**Step 2: Run RED**
- Run: `PYTHONPATH=src pytest -q tests/tools/test_t8n.py`
- Expected: failures showing missing validation behavior.

### Task 2: Implement minimal validation logic

**Files:**
- Modify: `src/neo/tools/t8n/t8n.py`

**Step 1: Expand `_validate_tx`**
- Add checks for:
  - non-negative int64 fees,
  - `validUntilBlock` expiry and max increment,
  - duplicate signer accounts,
  - legal `WitnessScope` mask and `GLOBAL` exclusivity,
  - signer field widths for accounts, contracts, and groups.

**Step 2: Keep receipt determinism**
- Ensure tx-hash computation remains robust for malformed inputs in permissive mode.

**Step 3: Run GREEN**
- Run: `PYTHONPATH=src pytest -q tests/tools/test_t8n.py`
- Expected: all `test_t8n` tests pass.

### Task 3: Extend conformance coverage

**Files:**
- Modify: `tests/tools/test_t8n.py`

**Step 1: Add runtime witness checks**
- Add checks for `System.Runtime.CheckWitness` behavior under:
  - `CALLED_BY_ENTRY`,
  - missing signer,
  - `CUSTOM_CONTRACTS` with matching allowed contract hash.

**Step 2: Validate strict-mode fail-fast**
- Add strict-mode test for invalid witness scopes raising `ValueError`.

### Task 4: Document and verify

**Files:**
- Modify: `docs/execution-spec.md`
- Modify: `docs/api.md`

**Step 1: Update docs**
- Document added envelope checks and strict/permissive behavior guarantees.

**Step 2: Run final gates**
- Run:
  - `ruff check src tests scripts`
  - `python3 scripts/check_mypy_regressions.py --baseline-file scripts/mypy-error-baseline.txt`
  - `PYTHONPATH=src pytest -q`
