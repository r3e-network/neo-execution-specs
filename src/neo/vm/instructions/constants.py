"""Push/constant instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Integer, ByteString, NULL
from neo.vm.opcode import OpCode

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def push_int(context: ExecutionContext, value: int) -> None:
    """Push an integer onto the stack."""
    context.evaluation_stack.push(Integer(value))


def push_data(context: ExecutionContext, data: bytes) -> None:
    """Push byte data onto the stack."""
    context.evaluation_stack.push(ByteString(data))


def push_null(context: ExecutionContext) -> None:
    """Push null onto the stack."""
    context.evaluation_stack.push(NULL)
