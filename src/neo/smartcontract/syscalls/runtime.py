"""Runtime syscalls."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


def runtime_get_trigger(engine: ApplicationEngine) -> None:
    """System.Runtime.GetTrigger"""
    from neo.vm.types import Integer
    engine.current_context.evaluation_stack.push(Integer(engine.trigger))


def runtime_get_time(engine: ApplicationEngine) -> None:
    """System.Runtime.GetTime"""
    from neo.vm.types import Integer
    # Placeholder - would get block time
    engine.current_context.evaluation_stack.push(Integer(0))
