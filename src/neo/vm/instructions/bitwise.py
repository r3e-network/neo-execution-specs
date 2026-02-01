"""Bitwise instructions for NeoVM.

This module implements all bitwise opcodes (0x90-0x98):
- INVERT: Bitwise NOT
- AND, OR, XOR: Bitwise operations
- EQUAL, NOTEQUAL: Equality comparison
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Integer, Boolean

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def invert(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Bitwise NOT - flip all bits."""
    x = engine.pop().get_integer()
    engine.push(Integer(~x))


def and_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Bitwise AND."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(x1 & x2))


def or_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Bitwise OR."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(x1 | x2))


def xor(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Bitwise XOR."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(x1 ^ x2))


def equal(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Check if two items are equal."""
    x2 = engine.pop()
    x1 = engine.pop()
    engine.push(Boolean(x1.equals(x2, engine.limits)))


def notequal(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Check if two items are not equal."""
    x2 = engine.pop()
    x1 = engine.pop()
    engine.push(Boolean(not x1.equals(x2, engine.limits)))
