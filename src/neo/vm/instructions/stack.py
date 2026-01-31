"""Stack manipulation instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.exceptions import InvalidOperationException

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def depth(context: ExecutionContext) -> None:
    """Push stack depth."""
    from neo.vm.types import Integer
    context.evaluation_stack.push(Integer(len(context.evaluation_stack)))


def drop(context: ExecutionContext) -> None:
    """Remove top item."""
    context.evaluation_stack.pop()


def dup(context: ExecutionContext) -> None:
    """Duplicate top item."""
    item = context.evaluation_stack.peek()
    context.evaluation_stack.push(item)


def swap(context: ExecutionContext) -> None:
    """Swap top two items."""
    stack = context.evaluation_stack
    a = stack.pop()
    b = stack.pop()
    stack.push(a)
    stack.push(b)
