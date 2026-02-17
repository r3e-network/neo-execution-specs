# neo-t8n Execution Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `neo-t8n` execution output deterministic, protocol-aligned, and useful for Neo v3.9.1 conformance workflows.

**Architecture:** Run each transition script through `ApplicationEngine` with bound block/network context, then project VM output (`stack`, `notifications`) and post-state alloc back to the t8n account schema. Lock behavior with focused `tests/tools/test_t8n.py` coverage before implementation changes.

**Tech Stack:** Python 3.11+, `ApplicationEngine`, `MemorySnapshot`, `pytest`.

### Task 1: Lock behavior with failing tests

**Files:**
- Modify: `tests/tools/test_t8n.py`

**Step 1: Write failing tests**

Add tests for:
- HALT/FAULT receipt state,
- result stack projection,
- runtime notification projection,
- post-state alloc extraction shape,
- network forwarding via `System.Runtime.GetNetwork`.

**Step 2: Run test module to verify red**

Run: `PYTHONPATH=src pytest -q tests/tools/test_t8n.py`
Expected: failures proving missing behavior in current `neo-t8n`.

### Task 2: Implement runtime + projection hardening

**Files:**
- Modify: `src/neo/tools/t8n/t8n.py`
- Modify: `src/neo/tools/t8n/types.py`

**Step 1: Switch execution to ApplicationEngine**

Use `ApplicationEngine` instead of plain VM engine and bind:
- protocol settings,
- persisting block context from `env`,
- transaction script container.

**Step 2: Add receipt projections**

Project:
- top-first result stack (`type`/`value`),
- notification payloads (`contract`, `eventName`, typed `state`),
- fault exception text.

**Step 3: Fix alloc extraction**

Reconstruct post-state alloc as account entries rather than raw snapshot keys.

**Step 4: Run test module to verify green**

Run: `PYTHONPATH=src pytest -q tests/tools/test_t8n.py`
Expected: all tests pass.

### Task 3: Document execution-spec boundaries

**Files:**
- Modify: `docs/execution-spec.md`
- Modify: `docs/api.md`
- Modify: `README.md`

**Step 1: Document actual `neo-t8n` semantics**

Describe:
- execution context wiring,
- receipt model and typed projections,
- post-state alloc behavior,
- explicit non-goals (not full consensus tx validation).

**Step 2: Verify docs and tests**

Run:
- `PYTHONPATH=src pytest -q tests/tools/test_t8n.py`
- `ruff check src tests scripts` (or touched files)

Expected: passing checks and no lint regressions.
