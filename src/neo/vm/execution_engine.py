"""NeoVM Execution Engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Callable, Dict

from neo.vm.evaluation_stack import EvaluationStack
from neo.vm.limits import ExecutionEngineLimits
from neo.vm.opcode import OpCode
from neo.vm.types import Integer, ByteString, NULL


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
    
    def read_byte(self) -> int:
        """Read next byte."""
        self.ip += 1
        return self.script[self.ip]
    
    def read_int8(self) -> int:
        """Read signed 8-bit integer."""
        b = self.read_byte()
        return b if b < 128 else b - 256
    
    def read_int16(self) -> int:
        """Read signed 16-bit integer."""
        data = self.script[self.ip+1:self.ip+3]
        self.ip += 2
        return int.from_bytes(data, 'little', signed=True)
    
    def read_int32(self) -> int:
        """Read signed 32-bit integer."""
        data = self.script[self.ip+1:self.ip+5]
        self.ip += 4
        return int.from_bytes(data, 'little', signed=True)


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
            self.invocation_stack.pop()
            if not self.invocation_stack:
                self.state = VMState.HALT
            return
        
        opcode = context.current_instruction
        try:
            self._execute_opcode(opcode, context)
        except Exception as e:
            self.state = VMState.FAULT
            return
        
        context.ip += 1
    
    def _execute_opcode(self, opcode: int, context: ExecutionContext) -> None:
        """Execute a single opcode."""
        stack = context.evaluation_stack
        
        # Push constants
        if opcode == OpCode.PUSH0:
            stack.push(Integer(0))
        elif opcode == OpCode.PUSHM1:
            stack.push(Integer(-1))
        elif OpCode.PUSH1 <= opcode <= OpCode.PUSH16:
            stack.push(Integer(opcode - OpCode.PUSH0))
        elif opcode == OpCode.PUSHINT8:
            stack.push(Integer(context.read_int8()))
        elif opcode == OpCode.PUSHNULL:
            stack.push(NULL)
        
        # Stack ops
        elif opcode == OpCode.DROP:
            stack.pop()
        elif opcode == OpCode.DUP:
            stack.push(stack.peek())
        elif opcode == OpCode.SWAP:
            a, b = stack.pop(), stack.pop()
            stack.push(a)
            stack.push(b)
        
        # Numeric ops
        elif opcode == OpCode.ADD:
            b, a = stack.pop().get_integer(), stack.pop().get_integer()
            stack.push(Integer(a + b))
        elif opcode == OpCode.SUB:
            b, a = stack.pop().get_integer(), stack.pop().get_integer()
            stack.push(Integer(a - b))
        elif opcode == OpCode.MUL:
            b, a = stack.pop().get_integer(), stack.pop().get_integer()
            stack.push(Integer(a * b))
        elif opcode == OpCode.DIV:
            b, a = stack.pop().get_integer(), stack.pop().get_integer()
            stack.push(Integer(a // b))
        elif opcode == OpCode.MOD:
            b, a = stack.pop().get_integer(), stack.pop().get_integer()
            stack.push(Integer(a % b))
        elif opcode == OpCode.INC:
            a = stack.pop().get_integer()
            stack.push(Integer(a + 1))
        elif opcode == OpCode.DEC:
            a = stack.pop().get_integer()
            stack.push(Integer(a - 1))
        elif opcode == OpCode.NEGATE:
            a = stack.pop().get_integer()
            stack.push(Integer(-a))
        
        # Comparison ops
        elif opcode == OpCode.LT:
            from neo.vm.types import Boolean
            b, a = stack.pop().get_integer(), stack.pop().get_integer()
            stack.push(Boolean(a < b))
        elif opcode == OpCode.GT:
            from neo.vm.types import Boolean
            b, a = stack.pop().get_integer(), stack.pop().get_integer()
            stack.push(Boolean(a > b))
        elif opcode == OpCode.EQUAL:
            from neo.vm.types import Boolean
            b, a = stack.pop(), stack.pop()
            stack.push(Boolean(a == b))
        
        # Control flow
        elif opcode == OpCode.NOP:
            pass
        elif opcode == OpCode.RET:
            self.invocation_stack.pop()
            if not self.invocation_stack:
                self.state = VMState.HALT
