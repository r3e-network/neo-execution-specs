"""Numeric instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Integer
from neo.exceptions import InvalidOperationException

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def add(context: ExecutionContext) -> None:
    """Add top two integers."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Integer(a + b))


def sub(context: ExecutionContext) -> None:
    """Subtract top two integers."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Integer(a - b))


def mul(context: ExecutionContext) -> None:
    """Multiply top two integers."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Integer(a * b))


def div(context: ExecutionContext) -> None:
    """Divide top two integers."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    if b == 0:
        raise InvalidOperationException("Division by zero")
    stack.push(Integer(a // b))


def mod(context: ExecutionContext) -> None:
    """Modulo of top two integers."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    if b == 0:
        raise InvalidOperationException("Division by zero")
    stack.push(Integer(a % b))
