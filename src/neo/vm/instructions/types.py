"""Type instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Boolean, StackItemType, NULL

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def isnull(context: ExecutionContext) -> None:
    """Check if item is null."""
    item = context.evaluation_stack.pop()
    result = item is NULL or item.type == StackItemType.ANY
    context.evaluation_stack.push(Boolean(result))


def istype(context: ExecutionContext, item_type: int) -> None:
    """Check if item is of specified type."""
    item = context.evaluation_stack.pop()
    result = item.type == item_type
    context.evaluation_stack.push(Boolean(result))
