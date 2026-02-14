# State + Control Vector Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand executable spec vectors to cover additional Neo control-flow relational branches and deeper state-script execution paths.

**Architecture:** Add missing VM control-flow false-path vectors in `control_flow_deep.json`, add additional executable state vectors in `executable_state_deep.json`, and bind the new vectors into checklist coverage IDs so quality gates reflect the expanded corpus. Protect this with targeted tests that initially fail until vectors/manifests are updated.

**Tech Stack:** Python 3.11+, pytest, JSON vector fixtures, neo-diff vector loader/coverage tooling.

### Task 1: Add TDD Guardrails for New Vector Coverage

**Files:**
- Create: `tests/tools/test_vector_expansion.py`
- Test: `tests/tools/test_vector_expansion.py`

**Step 1: Write the failing test**

Add tests that assert required new vector names exist in:
- `tests/vectors/vm/control_flow_deep.json`
- `tests/vectors/state/executable_state_deep.json`
- `tests/vectors/checklist_coverage.json`

Expected required names:
- VM: `JMPGT_false`, `JMPGT_L_false`, `JMPGE_false`, `JMPGE_L_false`, `JMPLT_false`, `JMPLT_L_false`, `JMPLE_false`, `JMPLE_L_false`
- State: `STATE_exec_jmpgt_l_false`, `STATE_exec_packmap_size2`, `STATE_exec_initslot_starg0_roundtrip`, `STATE_exec_assertmsg_true`

**Step 2: Run test to verify it fails**

Run: `pytest tests/tools/test_vector_expansion.py -q`
Expected: FAIL because vectors are not yet present.

### Task 2: Add Missing VM Control-Flow False-Path Vectors

**Files:**
- Modify: `tests/vectors/vm/control_flow_deep.json`
- Test: `tests/tools/test_vector_expansion.py`

**Step 1: Add vector entries**

Append 8 vectors covering false-path behavior for short and long relational jumps:
- `JMPGT_false`
- `JMPGT_L_false`
- `JMPGE_false`
- `JMPGE_L_false`
- `JMPLT_false`
- `JMPLT_L_false`
- `JMPLE_false`
- `JMPLE_L_false`

Each vector should include valid script bytes and expected post stack.

**Step 2: Validate VM vector file**

Run: `cd tests/vectors && python3 validate.py vm/control_flow_deep.json`
Expected: PASS for all vectors in this file.

### Task 3: Add Executable Deep State Vectors + Coverage Manifest Links

**Files:**
- Modify: `tests/vectors/state/executable_state_deep.json`
- Modify: `tests/vectors/checklist_coverage.json`
- Test: `tests/tools/test_vector_expansion.py`

**Step 1: Add 4 executable state vectors**

Add vectors using executable scripts that already exercise stable VM behavior:
- `STATE_exec_jmpgt_l_false`
- `STATE_exec_packmap_size2`
- `STATE_exec_initslot_starg0_roundtrip`
- `STATE_exec_assertmsg_true`

Use same transaction/pre_state/post_state structural shape as existing `STATE_exec_*` vectors.

**Step 2: Update checklist coverage mappings**

Update manifest vectors for:
- `vm/control_flow/long_and_relational_jump_variants` (include new VM vectors)
- `vm/runtime/exception_handling` (attach runtime exception-flow vectors)
- `state/transaction_script_execution_deep_vectors` (include new state vectors)

**Step 3: Run targeted tests to verify they now pass**

Run: `pytest tests/tools/test_vector_expansion.py -q`
Expected: PASS.

### Task 4: Run Full Verification Gates

**Files:**
- No additional code changes
- Verify: repo quality gates

**Step 1: Vector validation**

Run: `cd tests/vectors && python3 validate.py`
Expected: all vectors pass.

**Step 2: Diff Python-only parity**

Run: `python3 -m neo.tools.diff.cli --vectors tests/vectors/vm --python-only`
Expected: all VM vectors pass.

**Step 3: Unit test suite**

Run: `python3 -m pytest -q`
Expected: full suite pass.

**Step 4: Checklist coverage gate**

Run: `python3 -m neo.tools.diff.coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md --coverage-manifest tests/vectors/checklist_coverage.json --vectors-root tests/vectors/`
Expected: 100% coverage, no unknown vectors.
