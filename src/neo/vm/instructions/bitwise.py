"""Bitwise instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Integer, Boolean

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def invert(context: ExecutionContext) -> None:
    """Bitwise NOT."""
    stack = context.evaluation_stack
    a = stack.pop().get_integer()
    stack.push(Integer(~a))


def and_op(context: ExecutionContext) -> None:
    """Bitwise AND."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Integer(a & b))


def or_op(context: ExecutionContext) -> None:
    """Bitwise OR."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Integer(a | b))


def xor_op(context: ExecutionContext) -> None:
    """Bitwise XOR."""
    stack = context.evaluation_stack
    b = stack.pop().get_integer()
    a = stack.pop().get_integer()
    stack.push(Integer(a ^ b))
