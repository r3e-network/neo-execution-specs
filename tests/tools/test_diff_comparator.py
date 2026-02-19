"""Tests for diff result comparator behavior."""

from __future__ import annotations

from neo.tools.diff.cli import create_parser
from neo.tools.diff.comparator import DiffType, ResultComparator
from neo.tools.diff.models import ExecutionResult, ExecutionSource, StackValue


def test_compare_halt_results_checks_stack_and_gas() -> None:
    comparator = ResultComparator(gas_tolerance=0)

    py_result = ExecutionResult(
        source=ExecutionSource.PYTHON_SPEC,
        state="HALT",
        gas_consumed=10,
        stack=[StackValue(type="Integer", value=1)],
    )
    cs_result = ExecutionResult(
        source=ExecutionSource.CSHARP_CLI,
        state="HALT",
        gas_consumed=12,
        stack=[StackValue(type="Integer", value=2)],
    )

    compared = comparator.compare("vector_halt", py_result, cs_result)

    diff_types = {difference.diff_type for difference in compared.differences}
    assert DiffType.STACK_VALUE in diff_types
    assert DiffType.GAS_MISMATCH in diff_types


def test_compare_fault_results_ignore_stack_and_gas_variance() -> None:
    comparator = ResultComparator(gas_tolerance=0)

    py_result = ExecutionResult(
        source=ExecutionSource.PYTHON_SPEC,
        state="FAULT",
        gas_consumed=7,
        stack=[],
    )
    cs_result = ExecutionResult(
        source=ExecutionSource.CSHARP_CLI,
        state="FAULT",
        gas_consumed=99,
        stack=[StackValue(type="Integer", value=123)],
    )

    compared = comparator.compare("vector_fault", py_result, cs_result)

    assert compared.is_match is True
    assert compared.differences == []


def test_compare_state_mismatch_is_still_reported() -> None:
    comparator = ResultComparator(gas_tolerance=0)

    py_result = ExecutionResult(
        source=ExecutionSource.PYTHON_SPEC,
        state="HALT",
        gas_consumed=0,
        stack=[StackValue(type="Integer", value=1)],
    )
    cs_result = ExecutionResult(
        source=ExecutionSource.CSHARP_CLI,
        state="FAULT",
        gas_consumed=0,
        stack=[],
    )

    compared = comparator.compare("vector_state", py_result, cs_result)

    assert compared.is_match is False
    assert len(compared.differences) == 1
    assert compared.differences[0].diff_type == DiffType.STATE_MISMATCH


def test_policy_governance_drift_can_be_ignored_when_enabled() -> None:
    comparator = ResultComparator(
        gas_tolerance=0,
        allow_policy_governance_drift=True,
    )

    py_result = ExecutionResult(
        source=ExecutionSource.PYTHON_SPEC,
        state="HALT",
        gas_consumed=0,
        stack=[StackValue(type="Integer", value=1000)],
    )
    cs_result = ExecutionResult(
        source=ExecutionSource.CSHARP_CLI,
        state="HALT",
        gas_consumed=0,
        stack=[StackValue(type="Integer", value=20)],
    )

    compared = comparator.compare(
        "Policy_getFeePerByte",
        py_result,
        cs_result,
        vector_metadata={
            "category": "native",
            "contract": "PolicyContract",
            "method": "getFeePerByte",
        },
    )

    assert compared.is_match is True
    assert compared.differences == []


def test_policy_governance_drift_ignore_is_contract_case_insensitive() -> None:
    comparator = ResultComparator(
        gas_tolerance=0,
        allow_policy_governance_drift=True,
    )

    py_result = ExecutionResult(
        source=ExecutionSource.PYTHON_SPEC,
        state="HALT",
        gas_consumed=0,
        stack=[StackValue(type="Integer", value=30)],
    )
    cs_result = ExecutionResult(
        source=ExecutionSource.CSHARP_CLI,
        state="HALT",
        gas_consumed=0,
        stack=[StackValue(type="Integer", value=1)],
    )

    compared = comparator.compare(
        "Policy_getExecFeeFactor",
        py_result,
        cs_result,
        vector_metadata={
            "category": "native",
            "contract": "policycontract",
            "method": "getExecFeeFactor",
        },
    )

    assert compared.is_match is True
    assert compared.differences == []


def test_policy_governance_drift_not_ignored_for_other_methods() -> None:
    comparator = ResultComparator(
        gas_tolerance=0,
        allow_policy_governance_drift=True,
    )

    py_result = ExecutionResult(
        source=ExecutionSource.PYTHON_SPEC,
        state="HALT",
        gas_consumed=0,
        stack=[StackValue(type="Integer", value=123)],
    )
    cs_result = ExecutionResult(
        source=ExecutionSource.CSHARP_CLI,
        state="HALT",
        gas_consumed=0,
        stack=[StackValue(type="Integer", value=999)],
    )

    compared = comparator.compare(
        "Policy_unrelated",
        py_result,
        cs_result,
        vector_metadata={
            "category": "native",
            "contract": "PolicyContract",
            "method": "isBlocked",
        },
    )

    assert compared.is_match is False
    assert compared.differences
    assert compared.differences[0].diff_type == DiffType.STACK_VALUE


def test_cli_parses_allow_policy_governance_drift_flag() -> None:
    parser = create_parser()
    args = parser.parse_args(["--vectors", "tests/vectors", "--allow-policy-governance-drift"])
    assert args.allow_policy_governance_drift is True
