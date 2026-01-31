"""Storage syscalls."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


def storage_get(engine: ApplicationEngine) -> None:
    """System.Storage.Get"""
    from neo.vm.types import ByteString
    # Placeholder implementation
    engine.current_context.evaluation_stack.push(ByteString(b""))


def storage_put(engine: ApplicationEngine) -> None:
    """System.Storage.Put"""
    stack = engine.current_context.evaluation_stack
    value = stack.pop()
    key = stack.pop()
    context = stack.pop()
    # Placeholder - would store to snapshot
