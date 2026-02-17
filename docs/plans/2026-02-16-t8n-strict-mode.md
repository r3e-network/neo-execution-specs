# neo-t8n Strict Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a user-selectable strict mode for `neo-t8n` that fails fast on transaction validation/execution errors.

**Architecture:** Keep current permissive default behavior (emit per-tx `FAULT` receipts and continue), and introduce a `strict` switch propagated from CLI to `T8N` core. In strict mode, errors are raised immediately so CLI exits non-zero.

**Tech Stack:** Python 3.11+, `argparse`, `pytest`.

### Task 1: Define strict-mode behavior with tests

**Files:**
- Modify: `tests/tools/test_t8n.py`
- Create: `tests/tools/test_t8n_cli.py`

**Step 1: Write failing core tests**
- Add tests for `T8N(..., strict=True)` raising on invalid script hex and expired `validUntilBlock`.

**Step 2: Verify red**
- Run: `PYTHONPATH=src pytest -q tests/tools/test_t8n.py`
- Expected: strict tests fail before implementation.

**Step 3: Write failing CLI tests**
- Add tests for:
  - default mode continues after invalid tx and writes FAULT+HALT receipts,
  - `--strict` exits with status `1` on invalid tx input.

### Task 2: Implement strict-mode plumbing

**Files:**
- Modify: `src/neo/tools/t8n/t8n.py`
- Modify: `src/neo/tools/t8n/cli.py`

**Step 1: Add `strict` option to core**
- Extend `T8N` constructor with `strict: bool = False`.
- In strict mode, re-raise tx validation/execution exceptions.

**Step 2: Add `--strict` CLI flag**
- Add parser option and pass through to `T8N`.

**Step 3: Verify green**
- Run: `PYTHONPATH=src pytest -q tests/tools/test_t8n.py tests/tools/test_t8n_cli.py`
- Expected: all strict-mode tests pass.

### Task 3: Document behavior

**Files:**
- Modify: `docs/execution-spec.md`
- Modify: `docs/api.md`
- Modify: `README.md`

**Step 1: Document modes**
- Note permissive default vs strict fail-fast semantics and user-facing impact.

**Step 2: Verify full gates**
- Run:
  - `ruff check src tests scripts`
  - `python3 scripts/check_mypy_regressions.py --baseline-file scripts/mypy-error-baseline.txt`
  - `PYTHONPATH=src pytest -q`
