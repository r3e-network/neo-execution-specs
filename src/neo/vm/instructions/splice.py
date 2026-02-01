"""Splice operations - string/byte manipulation."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import ByteString, Buffer, Integer
from neo.exceptions import InvalidOperationException

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def cat(context: ExecutionContext) -> None:
    """Concatenate two byte strings."""
    stack = context.evaluation_stack
    b = stack.pop()
    a = stack.pop()
    
    if hasattr(a, 'value') and hasattr(b, 'value'):
        result = bytes(a.value) + bytes(b.value)
        stack.push(ByteString(result))


def substr(context: ExecutionContext) -> None:
    """Get substring."""
    stack = context.evaluation_stack
    count = int(stack.pop().get_integer())
    index = int(stack.pop().get_integer())
    data = stack.pop()
    
    if hasattr(data, 'value'):
        result = bytes(data.value)[index:index+count]
        stack.push(ByteString(result))
