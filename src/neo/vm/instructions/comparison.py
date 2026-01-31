"""Comparison instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Integer, Boolean

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def lt(context: ExecutionContext) -> None:
    """Less than."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Boolean(a < b))


def le(context: ExecutionContext) -> None:
    """Less than or equal."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Boolean(a <= b))


def gt(context: ExecutionContext) -> None:
    """Greater than."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Boolean(a > b))


def ge(context: ExecutionContext) -> None:
    """Greater than or equal."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Boolean(a >= b))
