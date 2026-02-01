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
    
    # Constants
    MAX_STORAGE_KEY_SIZE = 64
    MAX_STORAGE_VALUE_SIZE = 65535
    MAX_EVENT_NAME = 32
    MAX_NOTIFICATION_SIZE = 1024
    FEE_FACTOR = 10000
    
    # Additional fields
    script_container: Optional[object] = None
    snapshot: Optional[object] = None
    invocation_counter: Dict[bytes, int] = field(default_factory=dict)
    
    @property
    def current_script_hash(self) -> Optional[UInt160]:
        """Get script hash of current context."""
        from neo.types import UInt160
        import hashlib
        ctx = self.current_context
        if ctx is None:
            return None
        h = hashlib.new('ripemd160', hashlib.sha256(ctx.script).digest()).digest()
        return UInt160(h)
    
    @property
    def calling_script_hash(self) -> Optional[UInt160]:
        """Get script hash of calling context."""
        if len(self.invocation_stack) < 2:
            return None
        from neo.types import UInt160
        import hashlib
        ctx = self.invocation_stack[-2]
        h = hashlib.new('ripemd160', hashlib.sha256(ctx.script).digest()).digest()
        return UInt160(h)
    
    @property
    def entry_script_hash(self) -> Optional[UInt160]:
        """Get script hash of entry context."""
        if not self.invocation_stack:
            return None
        from neo.types import UInt160
        import hashlib
        ctx = self.invocation_stack[0]
        h = hashlib.new('ripemd160', hashlib.sha256(ctx.script).digest()).digest()
        return UInt160(h)
    
    def get_invocation_counter(self) -> int:
        """Get invocation counter for current script."""
        script_hash = self.current_script_hash
        if script_hash is None:
            return 0
        key = script_hash.data
        if key not in self.invocation_counter:
            self.invocation_counter[key] = 1
        return self.invocation_counter[key]
