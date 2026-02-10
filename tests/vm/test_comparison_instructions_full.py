"""Tests for VM comparison instructions (lt, le, gt, ge).

Covers all four comparison opcodes with positive, negative, equal,
and boundary cases.
"""

from __future__ import annotations

import pytest

from neo.vm.execution_context import ExecutionContext
from neo.vm.types import Integer, Boolean
from neo.vm.instructions.comparison import lt, le, gt, ge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(*values: int) -> ExecutionContext:
    """Create context with integers pushed in order (first pushed = bottom)."""
    ctx = ExecutionContext(script=b"\x00")
    for v in values:
        ctx.evaluation_stack.push(Integer(v))
    return ctx


def _result(ctx: ExecutionContext) -> bool:
    """Pop and return the boolean result from the stack."""
    return ctx.evaluation_stack.pop().get_boolean()


# ---------------------------------------------------------------------------
# LT tests
# ---------------------------------------------------------------------------

class TestLt:
    """Less-than instruction."""

    def test_true_when_a_less_than_b(self):
        ctx = _ctx(10, 20)  # a=10, b=20
        lt(ctx)
        assert _result(ctx) is True

    def test_false_when_a_equals_b(self):
        ctx = _ctx(5, 5)
        lt(ctx)
        assert _result(ctx) is False

    def test_false_when_a_greater_than_b(self):
        ctx = _ctx(20, 10)
        lt(ctx)
        assert _result(ctx) is False

    def test_negative_numbers(self):
        ctx = _ctx(-5, -1)
        lt(ctx)
        assert _result(ctx) is True


# ---------------------------------------------------------------------------
# LE tests
# ---------------------------------------------------------------------------

class TestLe:
    """Less-than-or-equal instruction."""

    def test_true_when_a_less_than_b(self):
        ctx = _ctx(10, 20)
        le(ctx)
        assert _result(ctx) is True

    def test_true_when_equal(self):
        ctx = _ctx(5, 5)
        le(ctx)
        assert _result(ctx) is True

    def test_false_when_a_greater_than_b(self):
        ctx = _ctx(20, 10)
        le(ctx)
        assert _result(ctx) is False


# ---------------------------------------------------------------------------
# GT tests
# ---------------------------------------------------------------------------

class TestGt:
    """Greater-than instruction."""

    def test_true_when_a_greater_than_b(self):
        ctx = _ctx(20, 10)
        gt(ctx)
        assert _result(ctx) is True

    def test_false_when_equal(self):
        ctx = _ctx(5, 5)
        gt(ctx)
        assert _result(ctx) is False

    def test_false_when_a_less_than_b(self):
        ctx = _ctx(10, 20)
        gt(ctx)
        assert _result(ctx) is False


# ---------------------------------------------------------------------------
# GE tests
# ---------------------------------------------------------------------------

class TestGe:
    """Greater-than-or-equal instruction."""

    def test_true_when_a_greater_than_b(self):
        ctx = _ctx(20, 10)
        ge(ctx)
        assert _result(ctx) is True

    def test_true_when_equal(self):
        ctx = _ctx(5, 5)
        ge(ctx)
        assert _result(ctx) is True

    def test_false_when_a_less_than_b(self):
        ctx = _ctx(10, 20)
        ge(ctx)
        assert _result(ctx) is False

    def test_zero_comparison(self):
        ctx = _ctx(0, 0)
        ge(ctx)
        assert _result(ctx) is True
