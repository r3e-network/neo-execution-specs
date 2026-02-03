"""Push/constant instructions for NeoVM.

This module implements all constant-pushing opcodes (0x00-0x20):
- PUSHINT8-256: Push signed integers of various sizes
- PUSHT/PUSHF: Push boolean true/false
- PUSHA: Push a pointer address
- PUSHNULL: Push null
- PUSHDATA1-4: Push byte arrays with length prefix
- PUSHM1, PUSH0-16: Push small integer constants
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Integer, ByteString, Boolean, NULL, Pointer

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def pushint8(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push a 1-byte signed integer onto the stack.
    
    Operand: 1 byte (signed)
    Push: 1 item
    Pop: 0 items
    """
    value = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.push(Integer(value))


def pushint16(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push a 2-byte signed integer onto the stack.
    
    Operand: 2 bytes (signed)
    Push: 1 item
    Pop: 0 items
    """
    value = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.push(Integer(value))


def pushint32(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push a 4-byte signed integer onto the stack.
    
    Operand: 4 bytes (signed)
    Push: 1 item
    Pop: 0 items
    """
    value = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.push(Integer(value))


def pushint64(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push an 8-byte signed integer onto the stack.
    
    Operand: 8 bytes (signed)
    Push: 1 item
    Pop: 0 items
    """
    value = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.push(Integer(value))


def pushint128(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push a 16-byte signed integer onto the stack.
    
    Operand: 16 bytes (signed)
    Push: 1 item
    Pop: 0 items
    """
    value = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.push(Integer(value))


def pushint256(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push a 32-byte signed integer onto the stack.
    
    Operand: 32 bytes (signed)
    Push: 1 item
    Pop: 0 items
    """
    value = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.push(Integer(value))


def pusht(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push boolean true onto the stack.
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(Boolean(True))


def pushf(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push boolean false onto the stack.
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(Boolean(False))


def pusha(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push a pointer address onto the stack.
    
    Converts a 4-byte offset to a Pointer and pushes it.
    The offset is relative to the current instruction pointer.
    
    Operand: 4 bytes (signed offset)
    Push: 1 item
    Pop: 0 items
    
    Raises:
        InvalidOperationException: If the resulting position is invalid.
    """
    offset = int.from_bytes(instruction.operand, 'little', signed=True)
    position = engine.current_context.ip + offset
    
    if position < 0 or position > len(engine.current_context.script):
        raise Exception(f"Bad pointer address: {position}")
    
    engine.push(Pointer(engine.current_context.script, position))


def pushnull(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push null onto the stack.
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(NULL)


def pushdata1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push byte data onto the stack (1-byte length prefix).
    
    The first byte of the operand specifies the length of the data.
    
    Push: 1 item
    Pop: 0 items
    """
    # Skip the 1-byte length prefix
    data = instruction.operand[1:]
    engine.limits.assert_max_item_size(len(data))
    engine.push(ByteString(data))


def pushdata2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push byte data onto the stack (2-byte length prefix).
    
    The first two bytes of the operand specify the length of the data.
    
    Push: 1 item
    Pop: 0 items
    """
    # Skip the 2-byte length prefix
    data = instruction.operand[2:]
    engine.limits.assert_max_item_size(len(data))
    engine.push(ByteString(data))


def pushdata4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push byte data onto the stack (4-byte length prefix).
    
    The first four bytes of the operand specify the length of the data.
    
    Push: 1 item
    Pop: 0 items
    """
    # Skip the 4-byte length prefix
    data = instruction.operand[4:]
    engine.limits.assert_max_item_size(len(data))
    engine.push(ByteString(data))


def pushm1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push -1 onto the stack.
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(Integer(-1))


def push0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 0 onto the stack.
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(Integer(0))


def push1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 1 onto the stack."""
    engine.push(Integer(1))


def push2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 2 onto the stack."""
    engine.push(Integer(2))


def push3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 3 onto the stack."""
    engine.push(Integer(3))


def push4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 4 onto the stack."""
    engine.push(Integer(4))


def push5(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 5 onto the stack."""
    engine.push(Integer(5))


def push6(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 6 onto the stack."""
    engine.push(Integer(6))


def push7(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 7 onto the stack."""
    engine.push(Integer(7))


def push8(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 8 onto the stack."""
    engine.push(Integer(8))


def push9(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 9 onto the stack."""
    engine.push(Integer(9))


def push10(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 10 onto the stack."""
    engine.push(Integer(10))


def push11(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 11 onto the stack."""
    engine.push(Integer(11))


def push12(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 12 onto the stack."""
    engine.push(Integer(12))


def push13(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 13 onto the stack."""
    engine.push(Integer(13))


def push14(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 14 onto the stack."""
    engine.push(Integer(14))


def push15(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 15 onto the stack."""
    engine.push(Integer(15))


def push16(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push 16 onto the stack."""
    engine.push(Integer(16))
