"""Compound type instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Array, Struct, Map, Integer

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def newarray0(context: ExecutionContext) -> None:
    """Create empty array."""
    context.evaluation_stack.push(Array())


def newarray(context: ExecutionContext) -> None:
    """Create array with size."""
    from neo.vm.types import NULL
    size = int(context.evaluation_stack.pop().get_integer())
    items = [NULL for _ in range(size)]
    context.evaluation_stack.push(Array(items))


def newstruct0(context: ExecutionContext) -> None:
    """Create empty struct."""
    context.evaluation_stack.push(Struct())


def newmap(context: ExecutionContext) -> None:
    """Create empty map."""
    context.evaluation_stack.push(Map())


def size(context: ExecutionContext) -> None:
    """Get size of compound type."""
    item = context.evaluation_stack.pop()
    context.evaluation_stack.push(Integer(len(item)))
