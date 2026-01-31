"""NeoVM Execution Engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional

from neo.vm.evaluation_stack import EvaluationStack
from neo.vm.limits import ExecutionEngineLimits


class VMState(IntEnum):
    """VM execution state."""
    NONE = 0
    HALT = 1
    FAULT = 2
    BREAK = 4


@dataclass
class ExecutionContext:
    """Execution context for a script."""
    script: bytes
    ip: int = 0
    evaluation_stack: EvaluationStack = field(default_factory=EvaluationStack)
    
    @property
    def current_instruction(self) -> int:
        """Get current opcode."""
        if self.ip >= len(self.script):
            return 0
        return self.script[self.ip]


@dataclass
class ExecutionEngine:
    """NeoVM execution engine."""
    
    limits: ExecutionEngineLimits = field(default_factory=ExecutionEngineLimits)
    invocation_stack: List[ExecutionContext] = field(default_factory=list)
    result_stack: EvaluationStack = field(default_factory=EvaluationStack)
    state: VMState = VMState.NONE
    
    @property
    def current_context(self) -> Optional[ExecutionContext]:
        """Get current execution context."""
        if not self.invocation_stack:
            return None
        return self.invocation_stack[-1]
    
    def load_script(self, script: bytes) -> ExecutionContext:
        """Load a script for execution."""
        context = ExecutionContext(script=script)
        self.invocation_stack.append(context)
        return context
    
    def execute(self) -> VMState:
        """Execute until completion."""
        self.state = VMState.NONE
        while self.state == VMState.NONE:
            self.execute_next()
        return self.state
    
    def execute_next(self) -> None:
        """Execute next instruction."""
        context = self.current_context
        if context is None:
            self.state = VMState.HALT
            return
        
        if context.ip >= len(context.script):
            self.state = VMState.HALT
            return
        
        # Get and execute opcode
        opcode = context.current_instruction
        self._execute_opcode(opcode, context)
        context.ip += 1
    
    def _execute_opcode(self, opcode: int, context: ExecutionContext) -> None:
        """Execute a single opcode."""
        from neo.vm.opcode import OpCode
        # Implementation will be added in Phase 2
        pass
