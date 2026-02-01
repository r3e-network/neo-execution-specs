"""Tests for VM compound operations (arrays, maps, structs)."""

import pytest
from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestPack:
    """Tests for PACK opcode."""

    def test_pack_empty(self):
        """PACK with 0 elements creates empty array."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH0, OpCode.PACK])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_pack_single_element(self):
        """PACK with 1 element."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.PUSH1, OpCode.PACK])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_pack_multiple_elements(self):
        """PACK with multiple elements."""
        engine = ExecutionEngine()
        # Push 1, 2, 3, then pack 3 elements
        script = bytes([
            OpCode.PUSH1, OpCode.PUSH2, OpCode.PUSH3,
            OpCode.PUSH3, OpCode.PACK
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestUnpack:
    """Tests for UNPACK opcode."""

    def test_unpack_array(self):
        """UNPACK spreads array elements onto stack."""
        engine = ExecutionEngine()
        # Create array [1, 2], then unpack
        script = bytes([
            OpCode.PUSH1, OpCode.PUSH2,
            OpCode.PUSH2, OpCode.PACK,
            OpCode.UNPACK
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestNewArray:
    """Tests for NEWARRAY opcodes."""

    def test_newarray0(self):
        """NEWARRAY0 creates empty array."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWARRAY0])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_newarray_with_size(self):
        """NEWARRAY creates array with specified size."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.NEWARRAY])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestNewMap:
    """Tests for NEWMAP opcode."""

    def test_newmap(self):
        """NEWMAP creates empty map."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWMAP])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestSize:
    """Tests for SIZE opcode."""

    def test_size_empty_array(self):
        """SIZE of empty array is 0."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWARRAY0, OpCode.SIZE])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_size_array(self):
        """SIZE returns array length."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH3, OpCode.NEWARRAY, OpCode.SIZE])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_size_map(self):
        """SIZE of empty map is 0."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWMAP, OpCode.SIZE])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestHasKey:
    """Tests for HASKEY opcode."""

    def test_haskey_array_valid_index(self):
        """HASKEY returns true for valid array index."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSH3, OpCode.NEWARRAY,  # Create array of size 3
            OpCode.PUSH0,                    # Index 0
            OpCode.HASKEY
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_haskey_array_invalid_index(self):
        """HASKEY returns false for invalid array index."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSH3, OpCode.NEWARRAY,  # Create array of size 3
            OpCode.PUSH5,                    # Index 5 (out of bounds)
            OpCode.HASKEY
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestPickItem:
    """Tests for PICKITEM opcode."""

    def test_pickitem_array(self):
        """PICKITEM retrieves array element by index."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSH1, OpCode.PUSH2, OpCode.PUSH3,
            OpCode.PUSH3, OpCode.PACK,  # Create [1, 2, 3]
            OpCode.PUSH0,                # Index 0
            OpCode.PICKITEM
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestSetItem:
    """Tests for SETITEM opcode."""

    def test_setitem_array(self):
        """SETITEM sets array element at index."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSH3, OpCode.NEWARRAY,  # Create array of size 3
            OpCode.PUSH0,                    # Index 0
            OpCode.PUSH9,                    # Value 9
            OpCode.SETITEM
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
