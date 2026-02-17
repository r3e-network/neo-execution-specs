"""Execution context for NeoVM.

This module implements the ExecutionContext class which represents a frame
in the VM execution stack, including support for exception handling.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from neo.vm.evaluation_stack import EvaluationStack
from neo.vm.exception_handling import (
    TryStack,
)
from neo.vm.slot import Slot

if TYPE_CHECKING:
    pass

@dataclass
class Instruction:
    """Represents a single VM instruction.
    
    Attributes:
        opcode: The opcode byte.
        operand: The operand bytes (if any).
        position: Position in the script.
    """
    opcode: int
    operand: bytes = b''
    position: int = 0
    
    @property
    def size(self) -> int:
        """Get the total size of this instruction in bytes."""
        return 1 + len(self.operand)
    
    @property
    def token_u8(self) -> int:
        """Get first operand byte as unsigned."""
        if len(self.operand) < 1:
            return 0
        return self.operand[0]
    
    @property
    def token_i8(self) -> int:
        """Get first operand byte as signed."""
        if len(self.operand) < 1:
            return 0
        val = self.operand[0]
        return val if val < 128 else val - 256
    
    @property
    def token_i8_1(self) -> int:
        """Get second operand byte as signed."""
        if len(self.operand) < 2:
            return 0
        val = self.operand[1]
        return val if val < 128 else val - 256
    
    @property
    def token_i32(self) -> int:
        """Get first 4 operand bytes as signed 32-bit integer."""
        if len(self.operand) < 4:
            return 0
        return int.from_bytes(self.operand[0:4], 'little', signed=True)
    
    @property
    def token_i32_1(self) -> int:
        """Get bytes 4-7 as signed 32-bit integer."""
        if len(self.operand) < 8:
            return 0
        return int.from_bytes(self.operand[4:8], 'little', signed=True)
    
    @property
    def token_u32(self) -> int:
        """Get first 4 operand bytes as unsigned 32-bit integer."""
        if len(self.operand) < 4:
            return 0
        return int.from_bytes(self.operand[0:4], 'little', signed=False)

class SharedStates:
    """Shared state between cloned execution contexts.
    
    When a context is cloned (e.g., for CALL), the clone shares the same
    script, evaluation stack, and static fields with the original.
    """
    
    def __init__(self, script: bytes, reference_counter: Any = None) -> None:
        self.script = script
        self.evaluation_stack = EvaluationStack()
        self.static_fields: Slot | None = None
        self.states: dict[object, Any] = {}
        self.reference_counter = reference_counter

class ExecutionContext:
    """Represents a frame in the VM execution stack.
    
    Each context has its own instruction pointer, local variables, and
    arguments, but shares the evaluation stack and static fields with
    cloned contexts.
    
    Attributes:
        script: The script being executed.
        ip: Current instruction pointer.
        evaluation_stack: The evaluation stack (shared with clones).
        static_fields: Static field slot (shared with clones).
        local_variables: Local variable slot.
        arguments: Argument slot.
        try_stack: Stack of exception handling contexts.
        rv_count: Expected return value count (-1 for any).
    """
    
    def __init__(
        self,
        script: bytes,
        rv_count: int = 0,
        reference_counter: Any = None,
        _shared_states: SharedStates | None = None,
        _initial_position: int = 0,
    ) -> None:
        """Initialize a new execution context.
        
        Args:
            script: The script to execute.
            rv_count: Expected return value count.
            reference_counter: Reference counter for compound types.
            _shared_states: Internal - shared states for cloning.
            _initial_position: Internal - initial IP for cloning.
        """
        if rv_count < -1 or rv_count > 65535:
            raise ValueError(f"rv_count out of range: {rv_count}")
        
        if _shared_states is not None:
            self._shared_states = _shared_states
        else:
            self._shared_states = SharedStates(script, reference_counter)
        
        self._ip = _initial_position
        self.rv_count = rv_count
        self.local_variables: Slot | None = None
        self.arguments: Slot | None = None
        self.try_stack: TryStack | None = None
    
    @property
    def script(self) -> bytes:
        """Get the script being executed."""
        return self._shared_states.script
    
    @property
    def evaluation_stack(self) -> EvaluationStack:
        """Get the evaluation stack."""
        return self._shared_states.evaluation_stack
    
    @property
    def static_fields(self) -> Slot | None:
        """Get the static fields slot."""
        return self._shared_states.static_fields
    
    @static_fields.setter
    def static_fields(self, value: Slot | None) -> None:
        """Set the static fields slot."""
        self._shared_states.static_fields = value
    
    @property
    def ip(self) -> int:
        """Get the instruction pointer."""
        return self._ip
    
    @ip.setter
    def ip(self, value: int) -> None:
        """Set the instruction pointer."""
        if value < 0 or value > len(self.script):
            raise ValueError(f"IP out of bounds: {value}/{len(self.script)}")
        self._ip = value
    
    @property
    def current_instruction(self) -> Instruction | None:
        """Get the current instruction."""
        return self.get_instruction(self._ip)
    
    @property
    def next_instruction(self) -> Instruction | None:
        """Get the next instruction."""
        current = self.current_instruction
        if current is None:
            return None
        return self.get_instruction(self._ip + current.size)
    
    def get_instruction(self, position: int) -> Instruction | None:
        """Get instruction at the specified position."""
        if position >= len(self.script):
            return None
        return _parse_instruction(self.script, position)
    
    def clone(self, initial_position: int | None = None) -> ExecutionContext:
        """Clone this context, sharing script, stack, and static fields.
        
        Args:
            initial_position: IP for the new context (default: current IP).
            
        Returns:
            A new ExecutionContext sharing state with this one.
        """
        if initial_position is None:
            initial_position = self._ip
        return ExecutionContext(
            script=self.script,
            rv_count=-1,
            _shared_states=self._shared_states,
            _initial_position=initial_position,
        )
    
    def move_next(self) -> bool:
        """Move to the next instruction.

        Returns:
            True if there is a next instruction, False otherwise.
        """
        current = self.current_instruction
        if current is None:
            return False
        new_ip = self._ip + current.size
        # Clamp to script length (end-of-script is valid sentinel)
        if new_ip > len(self.script):
            new_ip = len(self.script)
        self._ip = new_ip
        return self._ip < len(self.script)
    
    def get_state(self, state_type: type) -> Any:
        """Get custom state of the specified type, creating if needed."""
        if state_type not in self._shared_states.states:
            self._shared_states.states[state_type] = state_type()
        return self._shared_states.states[state_type]

def _parse_instruction(script: bytes, position: int) -> Instruction:
    """Parse an instruction from the script at the given position."""
    
    opcode = script[position]
    operand = b''
    
    # Determine operand size based on opcode
    operand_size = _get_operand_size(opcode, script, position)
    if operand_size > 0:
        operand = script[position + 1:position + 1 + operand_size]
    
    return Instruction(opcode=opcode, operand=operand, position=position)

def _get_operand_size(opcode: int, script: bytes, position: int) -> int:
    """Get the operand size for an opcode."""
    from neo.vm.opcode import OpCode

    try:
        op = OpCode(opcode)
    except ValueError:
        return 0

    # Variable-length operands
    if op == OpCode.PUSHDATA1:
        return 1 + script[position + 1] if position + 1 < len(script) else 0
    elif op == OpCode.PUSHDATA2:
        if position + 2 < len(script):
            length = int.from_bytes(script[position + 1:position + 3], 'little')
            return 2 + length
        return 0
    elif op == OpCode.PUSHDATA4:
        if position + 4 < len(script):
            length = int.from_bytes(script[position + 1:position + 5], 'little')
            return 4 + length
        return 0
    
    # Fixed-size operands
    operand_sizes = {
        OpCode.PUSHINT8: 1,
        OpCode.PUSHINT16: 2,
        OpCode.PUSHINT32: 4,
        OpCode.PUSHINT64: 8,
        OpCode.PUSHINT128: 16,
        OpCode.PUSHINT256: 32,
        OpCode.PUSHA: 4,
        OpCode.JMP: 1,
        OpCode.JMP_L: 4,
        OpCode.JMPIF: 1,
        OpCode.JMPIF_L: 4,
        OpCode.JMPIFNOT: 1,
        OpCode.JMPIFNOT_L: 4,
        OpCode.JMPEQ: 1,
        OpCode.JMPEQ_L: 4,
        OpCode.JMPNE: 1,
        OpCode.JMPNE_L: 4,
        OpCode.JMPGT: 1,
        OpCode.JMPGT_L: 4,
        OpCode.JMPGE: 1,
        OpCode.JMPGE_L: 4,
        OpCode.JMPLT: 1,
        OpCode.JMPLT_L: 4,
        OpCode.JMPLE: 1,
        OpCode.JMPLE_L: 4,
        OpCode.CALL: 1,
        OpCode.CALL_L: 4,
        OpCode.CALLT: 2,
        OpCode.TRY: 2,
        OpCode.TRY_L: 8,
        OpCode.ENDTRY: 1,
        OpCode.ENDTRY_L: 4,
        OpCode.SYSCALL: 4,
        OpCode.INITSSLOT: 1,
        OpCode.INITSLOT: 2,
        OpCode.LDSFLD: 1,
        OpCode.STSFLD: 1,
        OpCode.LDLOC: 1,
        OpCode.STLOC: 1,
        OpCode.LDARG: 1,
        OpCode.STARG: 1,
        OpCode.NEWARRAY_T: 1,
        OpCode.ISTYPE: 1,
        OpCode.CONVERT: 1,
    }
    
    return operand_sizes.get(op, 0)
