"""Splice instructions for NeoVM.

This module implements all splice opcodes (0x88-0x8E):
- NEWBUFFER: Create new buffer
- MEMCPY: Copy bytes between buffers
- CAT: Concatenate byte strings
- SUBSTR: Extract substring
- LEFT, RIGHT: Extract from left/right
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Buffer

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def newbuffer(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create a new buffer of specified size."""
    length = int(engine.pop().get_integer())
    if length < 0:
        raise Exception(f"Buffer length cannot be negative: {length}")
    engine.limits.assert_max_item_size(length)
    engine.push(Buffer(length))


def memcpy(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Copy bytes from source to destination buffer."""
    count = int(engine.pop().get_integer())
    if count < 0:
        raise Exception(f"Count cannot be negative for MEMCPY: {count}")
    si = int(engine.pop().get_integer())
    if si < 0:
        raise Exception(f"Source index cannot be negative: {si}")
    src = engine.pop().get_span()
    if si + count > len(src):
        raise Exception(f"Source range out of bounds")
    di = int(engine.pop().get_integer())
    if di < 0:
        raise Exception(f"Destination index cannot be negative: {di}")
    dst = engine.pop()
    if not isinstance(dst, Buffer):
        raise Exception("Destination must be a Buffer")
    if di + count > len(dst):
        raise Exception(f"Destination range out of bounds")
    dst.inner_buffer[di:di+count] = src[si:si+count]


def cat(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Concatenate two byte strings."""
    x2 = engine.pop().get_span()
    x1 = engine.pop().get_span()
    length = len(x1) + len(x2)
    engine.limits.assert_max_item_size(length)
    result = bytearray(length)
    result[0:len(x1)] = x1
    result[len(x1):] = x2
    engine.push(Buffer(bytes(result)))


def substr(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Extract substring from byte string."""
    count = int(engine.pop().get_integer())
    if count < 0:
        raise Exception(f"Count cannot be negative: {count}")
    index = int(engine.pop().get_integer())
    if index < 0:
        raise Exception(f"Index cannot be negative: {index}")
    x = engine.pop().get_span()
    if index + count > len(x):
        raise Exception(f"Range out of bounds")
    engine.push(Buffer(bytes(x[index:index+count])))


def left(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Extract leftmost bytes from byte string."""
    count = int(engine.pop().get_integer())
    if count < 0:
        raise Exception(f"Count cannot be negative: {count}")
    x = engine.pop().get_span()
    if count > len(x):
        raise Exception(f"Count out of range: {count}")
    engine.push(Buffer(bytes(x[:count])))


def right(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Extract rightmost bytes from byte string."""
    count = int(engine.pop().get_integer())
    if count < 0:
        raise Exception(f"Count cannot be negative: {count}")
    x = engine.pop().get_span()
    if count > len(x):
        raise Exception(f"Count out of range: {count}")
    if count == 0:
        engine.push(Buffer(b''))
    else:
        engine.push(Buffer(bytes(x[-count:])))
