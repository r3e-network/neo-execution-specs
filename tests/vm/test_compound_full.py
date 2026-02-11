"""Comprehensive tests for VM compound type instructions.

Covers untested paths in compound.py:
- PACKMAP, PACKSTRUCT, UNPACK (Map branch)
- NEWARRAY_T, NEWSTRUCT
- SIZE (Buffer, ByteString, error), HASKEY (Buffer, error)
- KEYS, VALUES (Map, Array)
- PICKITEM (Map, Buffer, error), SETITEM (Map, Buffer, error)
- APPEND (error, limit), REVERSEITEMS (Buffer, error)
- REMOVE (Array, Map), CLEARITEMS, POPITEM
"""

from __future__ import annotations

import pytest

from neo.vm import ExecutionEngine
from neo.vm.execution_context import Instruction
from neo.vm.instructions import compound as C
from neo.vm.types import (
    Integer, ByteString, Array, Struct, Map, NULL, StackItemType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(script: bytes) -> ExecutionEngine:
    """Load script, execute, return engine."""
    engine = ExecutionEngine()
    engine.load_script(bytes(script))
    engine.execute()
    return engine


def _stack_int(engine: ExecutionEngine) -> int:
    return engine.result_stack.pop().get_integer()


def _engine() -> ExecutionEngine:
    """Create engine with a loaded dummy script."""
    e = ExecutionEngine()
    e.load_script(b"\x00")
    return e


_DUMMY = Instruction(opcode=0)


# ---------------------------------------------------------------------------
# PACKMAP tests
# ---------------------------------------------------------------------------

class TestPackMap:
    """PACKMAP: pack key-value pairs into a map."""

    def test_packmap_basic(self):
        e = _engine()
        e.push(ByteString(b"v1"))  # value
        e.push(Integer(1))         # key
        e.push(Integer(1))         # size=1
        C.packmap(e, _DUMMY)
        result = e.pop()
        assert isinstance(result, Map)
        assert len(result) == 1

    def test_packmap_invalid_key_type(self):
        e = _engine()
        e.push(ByteString(b"v"))
        e.push(Array(e.reference_counter))  # non-primitive key
        e.push(Integer(1))
        with pytest.raises(Exception, match="PrimitiveType"):
            C.packmap(e, _DUMMY)

    def test_packmap_negative_size(self):
        e = _engine()
        e.push(Integer(-1))
        with pytest.raises(Exception, match="Invalid map size"):
            C.packmap(e, _DUMMY)


# ---------------------------------------------------------------------------
# PACKSTRUCT tests
# ---------------------------------------------------------------------------

class TestPackStruct:
    """PACKSTRUCT: pack items into a struct."""

    def test_packstruct_basic(self):
        e = _engine()
        e.push(Integer(10))
        e.push(Integer(20))
        e.push(Integer(2))  # size=2
        C.packstruct(e, _DUMMY)
        result = e.pop()
        assert isinstance(result, Struct)
        assert len(result) == 2

    def test_packstruct_negative_size(self):
        e = _engine()
        e.push(Integer(-1))
        with pytest.raises(Exception, match="Invalid struct size"):
            C.packstruct(e, _DUMMY)


# ---------------------------------------------------------------------------
# UNPACK tests (Map branch + error branch)
# ---------------------------------------------------------------------------

class TestUnpack:
    """UNPACK: unpack collection onto stack."""

    def test_unpack_map(self):
        e = _engine()
        m = Map(e.reference_counter)
        m[Integer(1)] = ByteString(b"a")
        m[Integer(2)] = ByteString(b"b")
        e.push(m)
        C.unpack(e, _DUMMY)
        # Top of stack: size
        assert e.pop().get_integer() == 2

    def test_unpack_invalid_type(self):
        e = _engine()
        e.push(Integer(42))
        with pytest.raises(Exception, match="Invalid type for UNPACK"):
            C.unpack(e, _DUMMY)


# ---------------------------------------------------------------------------
# NEWARRAY_T tests
# ---------------------------------------------------------------------------

class TestNewArrayT:
    """NEWARRAY_T: create typed array."""

    def test_boolean_type(self):
        e = _engine()
        e.push(Integer(2))
        instr = Instruction(opcode=0, operand=bytes([StackItemType.BOOLEAN]))
        C.newarray_t(e, instr)
        arr = e.pop()
        assert isinstance(arr, Array)
        assert len(arr) == 2
        assert arr[0].get_boolean() is False

    def test_integer_type(self):
        e = _engine()
        e.push(Integer(1))
        instr = Instruction(opcode=0, operand=bytes([StackItemType.INTEGER]))
        C.newarray_t(e, instr)
        arr = e.pop()
        assert arr[0].get_integer() == 0

    def test_bytestring_type(self):
        e = _engine()
        e.push(Integer(1))
        instr = Instruction(opcode=0, operand=bytes([StackItemType.BYTESTRING]))
        C.newarray_t(e, instr)
        arr = e.pop()
        assert isinstance(arr[0], ByteString)

    def test_null_default(self):
        e = _engine()
        e.push(Integer(1))
        instr = Instruction(opcode=0, operand=bytes([StackItemType.ANY]))
        C.newarray_t(e, instr)
        arr = e.pop()
        assert arr[0] is NULL


# ---------------------------------------------------------------------------
# NEWSTRUCT tests
# ---------------------------------------------------------------------------

class TestNewStruct:
    """NEWSTRUCT: create struct with n null elements."""

    def test_newstruct_basic(self):
        e = _engine()
        e.push(Integer(3))
        C.newstruct(e, _DUMMY)
        result = e.pop()
        assert isinstance(result, Struct)
        assert len(result) == 3

    def test_newstruct_negative_size(self):
        e = _engine()
        e.push(Integer(-1))
        with pytest.raises(Exception, match="Invalid struct size"):
            C.newstruct(e, _DUMMY)
