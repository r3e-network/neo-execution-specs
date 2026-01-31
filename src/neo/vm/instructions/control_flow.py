"""Control flow instructions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Boolean
from neo.exceptions import VMException

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def nop(context: ExecutionContext) -> None:
    """No operation."""
    pass


def jmp(context: ExecutionContext, offset: int) -> None:
    """Unconditional jump."""
    context.ip += offset - 1  # -1 because ip will be incremented after


def jmpif(context: ExecutionContext, offset: int) -> None:
    """Jump if true."""
    condition = context.evaluation_stack.pop().get_boolean()
    if condition:
        context.ip += offset - 1


def jmpifnot(context: ExecutionContext, offset: int) -> None:
    """Jump if false."""
    condition = context.evaluation_stack.pop().get_boolean()
    if not condition:
        context.ip += offset - 1


def ret(context: ExecutionContext) -> None:
    """Return from current context."""
    pass  # Handled by ExecutionEngine
