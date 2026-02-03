"""Tests for ExecutionResult."""

import pytest
from neo.smartcontract.execution_result import ExecutionResult


def test_result():
    """Test execution result."""
    r = ExecutionResult(state=1, gas_consumed=100)
    assert r.state == 1
