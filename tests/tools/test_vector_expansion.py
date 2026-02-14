"""TDD guardrails for control-flow and state vector expansion."""

from __future__ import annotations

import json
from pathlib import Path


_CONTROL_FLOW_DEEP_PATH = Path("tests/vectors/vm/control_flow_deep.json")
_STATE_DEEP_PATH = Path("tests/vectors/state/executable_state_deep.json")
_CHECKLIST_COVERAGE_PATH = Path("tests/vectors/checklist_coverage.json")

_REQUIRED_VM_VECTORS = {
    "JMPGT_false",
    "JMPGT_L_false",
    "JMPGE_false",
    "JMPGE_L_false",
    "JMPLT_false",
    "JMPLT_L_false",
    "JMPLE_false",
    "JMPLE_L_false",
}

_REQUIRED_STATE_VECTORS = {
    "STATE_exec_jmpgt_l_false",
    "STATE_exec_packmap_size2",
    "STATE_exec_initslot_starg0_roundtrip",
    "STATE_exec_assertmsg_true",
}


def _load_vector_names(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(vector["name"]) for vector in data["vectors"]}


def _load_coverage_vectors(path: Path, checklist_id: str) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = data[checklist_id]
    return set(entry.get("vectors", []))


def test_control_flow_deep_contains_required_relational_false_paths() -> None:
    names = _load_vector_names(_CONTROL_FLOW_DEEP_PATH)
    missing = _REQUIRED_VM_VECTORS - names
    assert not missing, f"Missing VM control-flow vectors: {sorted(missing)}"


def test_state_deep_contains_required_expansion_vectors() -> None:
    names = _load_vector_names(_STATE_DEEP_PATH)
    missing = _REQUIRED_STATE_VECTORS - names
    assert not missing, f"Missing state deep vectors: {sorted(missing)}"


def test_checklist_manifest_links_new_expansion_vectors() -> None:
    control_flow_vectors = _load_coverage_vectors(
        _CHECKLIST_COVERAGE_PATH,
        "vm/control_flow/long_and_relational_jump_variants",
    )
    state_deep_vectors = _load_coverage_vectors(
        _CHECKLIST_COVERAGE_PATH,
        "state/transaction_script_execution_deep_vectors",
    )

    missing_control = _REQUIRED_VM_VECTORS - control_flow_vectors
    missing_state = _REQUIRED_STATE_VECTORS - state_deep_vectors

    assert not missing_control, f"Checklist mapping missing VM vectors: {sorted(missing_control)}"
    assert not missing_state, f"Checklist mapping missing state vectors: {sorted(missing_state)}"
