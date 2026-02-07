"""Slot instructions for NeoVM.

This module implements all slot opcodes (0x56-0x87):
- INITSSLOT, INITSLOT: Initialize slots
- LDSFLD0-6, LDSFLD: Load static fields
- STSFLD0-6, STSFLD: Store static fields
- LDLOC0-6, LDLOC: Load local variables
- STLOC0-6, STLOC: Store local variables
- LDARG0-6, LDARG: Load arguments
- STARG0-6, STARG: Store arguments
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def _load_from_slot(engine: ExecutionEngine, slot, index: int) -> None:
    """Helper to load from a slot."""
    if slot is None:
        raise Exception("Slot has not been initialized.")
    if index < 0 or index >= len(slot):
        raise Exception(f"Index out of range: {index}")
    engine.push(slot[index])


def _store_to_slot(engine: ExecutionEngine, slot, index: int) -> None:
    """Helper to store to a slot."""
    if slot is None:
        raise Exception("Slot has not been initialized.")
    if index < 0 or index >= len(slot):
        raise Exception(f"Index out of range: {index}")
    slot[index] = engine.pop()


def initsslot(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Initialize static field slot."""
    ctx = engine.current_context
    if ctx.static_fields is not None:
        raise Exception("INITSSLOT cannot be executed twice.")
    count = instruction.operand[0]
    if count == 0:
        raise Exception("Invalid operand for INITSSLOT.")
    ctx.static_fields = engine.create_slot(count)


def initslot(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Initialize local and argument slots."""
    ctx = engine.current_context
    if ctx.local_variables is not None or ctx.arguments is not None:
        raise Exception("INITSLOT cannot be executed twice.")
    local_count = instruction.operand[0]
    arg_count = instruction.operand[1]
    if local_count == 0 and arg_count == 0:
        raise Exception("Invalid operand for INITSLOT.")
    if local_count > 0:
        ctx.local_variables = engine.create_slot(local_count)
    if arg_count > 0:
        items = []
        for _ in range(arg_count):
            items.append(engine.pop())
        # Reverse so arg0 = deepest stack item (first pushed)
        items.reverse()
        ctx.arguments = engine.create_slot_from_items(items)


# Static field load operations
def ldsfld0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at index 0."""
    _load_from_slot(engine, engine.current_context.static_fields, 0)


def ldsfld1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at index 1."""
    _load_from_slot(engine, engine.current_context.static_fields, 1)


def ldsfld2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at index 2."""
    _load_from_slot(engine, engine.current_context.static_fields, 2)


def ldsfld3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at index 3."""
    _load_from_slot(engine, engine.current_context.static_fields, 3)


def ldsfld4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at index 4."""
    _load_from_slot(engine, engine.current_context.static_fields, 4)


def ldsfld5(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at index 5."""
    _load_from_slot(engine, engine.current_context.static_fields, 5)


def ldsfld6(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at index 6."""
    _load_from_slot(engine, engine.current_context.static_fields, 6)


def ldsfld(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load static field at specified index."""
    index = instruction.operand[0]
    _load_from_slot(engine, engine.current_context.static_fields, index)


# Static field store operations
def stsfld0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at index 0."""
    _store_to_slot(engine, engine.current_context.static_fields, 0)


def stsfld1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at index 1."""
    _store_to_slot(engine, engine.current_context.static_fields, 1)


def stsfld2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at index 2."""
    _store_to_slot(engine, engine.current_context.static_fields, 2)


def stsfld3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at index 3."""
    _store_to_slot(engine, engine.current_context.static_fields, 3)


def stsfld4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at index 4."""
    _store_to_slot(engine, engine.current_context.static_fields, 4)


def stsfld5(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at index 5."""
    _store_to_slot(engine, engine.current_context.static_fields, 5)


def stsfld6(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at index 6."""
    _store_to_slot(engine, engine.current_context.static_fields, 6)


def stsfld(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to static field at specified index."""
    index = instruction.operand[0]
    _store_to_slot(engine, engine.current_context.static_fields, index)


# Local variable load operations
def ldloc0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at index 0."""
    _load_from_slot(engine, engine.current_context.local_variables, 0)


def ldloc1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at index 1."""
    _load_from_slot(engine, engine.current_context.local_variables, 1)


def ldloc2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at index 2."""
    _load_from_slot(engine, engine.current_context.local_variables, 2)


def ldloc3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at index 3."""
    _load_from_slot(engine, engine.current_context.local_variables, 3)


def ldloc4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at index 4."""
    _load_from_slot(engine, engine.current_context.local_variables, 4)


def ldloc5(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at index 5."""
    _load_from_slot(engine, engine.current_context.local_variables, 5)


def ldloc6(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at index 6."""
    _load_from_slot(engine, engine.current_context.local_variables, 6)


def ldloc(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load local variable at specified index."""
    index = instruction.operand[0]
    _load_from_slot(engine, engine.current_context.local_variables, index)


# Local variable store operations
def stloc0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at index 0."""
    _store_to_slot(engine, engine.current_context.local_variables, 0)


def stloc1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at index 1."""
    _store_to_slot(engine, engine.current_context.local_variables, 1)


def stloc2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at index 2."""
    _store_to_slot(engine, engine.current_context.local_variables, 2)


def stloc3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at index 3."""
    _store_to_slot(engine, engine.current_context.local_variables, 3)


def stloc4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at index 4."""
    _store_to_slot(engine, engine.current_context.local_variables, 4)


def stloc5(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at index 5."""
    _store_to_slot(engine, engine.current_context.local_variables, 5)


def stloc6(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at index 6."""
    _store_to_slot(engine, engine.current_context.local_variables, 6)


def stloc(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to local variable at specified index."""
    index = instruction.operand[0]
    _store_to_slot(engine, engine.current_context.local_variables, index)


# Argument load operations
def ldarg0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at index 0."""
    _load_from_slot(engine, engine.current_context.arguments, 0)


def ldarg1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at index 1."""
    _load_from_slot(engine, engine.current_context.arguments, 1)


def ldarg2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at index 2."""
    _load_from_slot(engine, engine.current_context.arguments, 2)


def ldarg3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at index 3."""
    _load_from_slot(engine, engine.current_context.arguments, 3)


def ldarg4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at index 4."""
    _load_from_slot(engine, engine.current_context.arguments, 4)


def ldarg5(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at index 5."""
    _load_from_slot(engine, engine.current_context.arguments, 5)


def ldarg6(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at index 6."""
    _load_from_slot(engine, engine.current_context.arguments, 6)


def ldarg(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Load argument at specified index."""
    index = instruction.operand[0]
    _load_from_slot(engine, engine.current_context.arguments, index)


# Argument store operations
def starg0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at index 0."""
    _store_to_slot(engine, engine.current_context.arguments, 0)


def starg1(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at index 1."""
    _store_to_slot(engine, engine.current_context.arguments, 1)


def starg2(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at index 2."""
    _store_to_slot(engine, engine.current_context.arguments, 2)


def starg3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at index 3."""
    _store_to_slot(engine, engine.current_context.arguments, 3)


def starg4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at index 4."""
    _store_to_slot(engine, engine.current_context.arguments, 4)


def starg5(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at index 5."""
    _store_to_slot(engine, engine.current_context.arguments, 5)


def starg6(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at index 6."""
    _store_to_slot(engine, engine.current_context.arguments, 6)


def starg(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Store to argument at specified index."""
    index = instruction.operand[0]
    _store_to_slot(engine, engine.current_context.arguments, index)
