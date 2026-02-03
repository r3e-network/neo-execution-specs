"""Neo N3 Application Engine - Smart contract execution.

Reference: Neo.SmartContract.ApplicationEngine
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import IntEnum

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode

if TYPE_CHECKING:
    from neo.types import UInt160


class TriggerType(IntEnum):
    """Trigger types for contract execution."""
    SYSTEM = 0x01
    VERIFICATION = 0x20
    APPLICATION = 0x40
    ALL = SYSTEM | VERIFICATION | APPLICATION


@dataclass
class ExecutionContext:
    """Execution context for a script."""
    script: bytes
    instruction_pointer: int = 0
    call_flags: int = 0x0F  # All
    
    @property
    def current_instruction(self) -> int:
        """Get current opcode."""
        if self.instruction_pointer >= len(self.script):
            return OpCode.RET
        return self.script[self.instruction_pointer]


@dataclass
class ApplicationEngine:
    """Neo N3 Application Engine."""
    
    trigger: TriggerType = TriggerType.APPLICATION
    gas_consumed: int = 0
    gas_limit: int = 10_000_000
    state: VMState = VMState.NONE
    snapshot: Any = None
    script_container: Any = None
    network: int = 860833102
    
    _contexts: List[ExecutionContext] = field(default_factory=list)
    _result_stack: List = field(default_factory=list)
    _notifications: List = field(default_factory=list)
    _logs: List = field(default_factory=list)
    _invocation_counters: Dict = field(default_factory=dict)
    
    def load_script(self, script: bytes) -> None:
        """Load script for execution."""
        ctx = ExecutionContext(script=script)
        self._contexts.append(ctx)
    
    @property
    def current_context(self) -> Optional[ExecutionContext]:
        """Get current context."""
        return self._contexts[-1] if self._contexts else None
    
    def execute(self) -> VMState:
        """Execute loaded scripts."""
        self.state = VMState.NONE
        while self._contexts and self.state == VMState.NONE:
            self._execute_next()
        if self.state == VMState.NONE:
            self.state = VMState.HALT
        return self.state
    
    def _execute_next(self) -> None:
        """Execute next instruction."""
        ctx = self.current_context
        if not ctx:
            return
        # Simplified execution
        ctx.instruction_pointer += 1
        if ctx.instruction_pointer >= len(ctx.script):
            self._contexts.pop()
    
    @property
    def current_script_hash(self) -> Optional["UInt160"]:
        """Get script hash of current context."""
        from neo.types import UInt160
        from neo.crypto import hash160
        ctx = self.current_context
        if ctx is None:
            return None
        return UInt160(hash160(ctx.script))
    
    @property
    def calling_script_hash(self) -> Optional["UInt160"]:
        """Get script hash of calling context."""
        from neo.types import UInt160
        from neo.crypto import hash160
        if len(self._contexts) < 2:
            return None
        ctx = self._contexts[-2]
        return UInt160(hash160(ctx.script))
    
    @property
    def entry_script_hash(self) -> Optional["UInt160"]:
        """Get script hash of entry context."""
        from neo.types import UInt160
        from neo.crypto import hash160
        if not self._contexts:
            return None
        ctx = self._contexts[0]
        return UInt160(hash160(ctx.script))
    
    def add_gas(self, amount: int) -> None:
        """Add gas consumption."""
        self.gas_consumed += amount
        if self.gas_consumed > self.gas_limit:
            raise Exception("Out of gas")
