"""Application Engine - extends ExecutionEngine with blockchain interaction."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.smartcontract.call_flags import CallFlags
from neo.smartcontract.trigger import TriggerType

if TYPE_CHECKING:
    from neo.types import UInt160


@dataclass
class Notification:
    """Contract notification event."""
    script_hash: UInt160
    event_name: str
    state: List


@dataclass
class ApplicationEngine(ExecutionEngine):
    """Execution engine with blockchain interaction."""
    
    trigger: TriggerType = TriggerType.APPLICATION
    gas_consumed: int = 0
    gas_limit: int = 0
    notifications: List[Notification] = field(default_factory=list)
    
    def add_gas(self, gas: int) -> None:
        """Consume gas."""
        self.gas_consumed += gas
        if self.gas_limit > 0 and self.gas_consumed > self.gas_limit:
            from neo.exceptions import OutOfGasException
            raise OutOfGasException()
