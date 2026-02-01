"""Slot operations - local variables, arguments, static fields."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionContext


def ldloc(context: ExecutionContext, index: int) -> None:
    """Load local variable."""
    # Placeholder - needs Slot implementation
    pass


def stloc(context: ExecutionContext, index: int) -> None:
    """Store local variable."""
    # Placeholder - needs Slot implementation
    pass
