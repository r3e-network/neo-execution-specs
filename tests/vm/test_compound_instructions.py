"""Tests for compound type instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode
from neo.vm.types import Integer, Array, Map, Struct, ByteString


class TestArrayOperations:
    """Test array operations."""
    
    def test_newarray0(self):
        """Test NEWARRAY0 creates empty array."""
        script = bytes([OpCode.NEWARRAY0])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert isinstance(result, Array)
        assert len(result) == 0
    
    def test_newarray(self):
        """Test NEWARRAY creates array with size."""
        script = bytes([
            OpCode.PUSH3,    # size = 3
            OpCode.NEWARRAY,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert isinstance(result, Array)
        assert len(result) == 3
    
    def test_pack(self):
        """Test PACK creates array from stack items."""
        script = bytes([
            OpCode.PUSH1,
            OpCode.PUSH2,
            OpCode.PUSH3,
            OpCode.PUSH3,    # count = 3
            OpCode.PACK,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert isinstance(result, Array)
        assert len(result) == 3
    
    def test_unpack(self):
        """Test UNPACK extracts array items to stack."""
        script = bytes([
            OpCode.PUSH1,
            OpCode.PUSH2,
            OpCode.PUSH2,
            OpCode.PACK,
            OpCode.UNPACK,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        # Stack should have: count, item1, item2
        assert engine.result_stack.peek(0).get_integer() == 2  # count
    
    def test_size_array(self):
        """Test SIZE on array."""
        script = bytes([
            OpCode.PUSH1,
            OpCode.PUSH2,
            OpCode.PUSH3,
            OpCode.PUSH3,
            OpCode.PACK,
            OpCode.SIZE,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 3
    
    def test_append(self):
        """Test APPEND adds item to array."""
        script = bytes([
            OpCode.NEWARRAY0,
            OpCode.DUP,
            OpCode.PUSH5,    # Use valid opcode
            OpCode.APPEND,
            OpCode.SIZE,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 1


class TestMapOperations:
    """Test map operations."""
    
    def test_newmap(self):
        """Test NEWMAP creates empty map."""
        script = bytes([OpCode.NEWMAP])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert isinstance(result, Map)
        assert len(result) == 0
    
    def test_setitem_map(self):
        """Test SETITEM on map."""
        script = bytes([
            OpCode.NEWMAP,
            OpCode.DUP,
            0x0c, 1, ord('k'),  # PUSHDATA1 "k"
            OpCode.PUSH5,       # Use valid opcode
            OpCode.SETITEM,
            OpCode.SIZE,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 1
    
    def test_haskey_map(self):
        """Test HASKEY on map."""
        script = bytes([
            OpCode.NEWMAP,
            OpCode.DUP,
            0x0c, 1, ord('k'),
            OpCode.PUSH1,
            OpCode.SETITEM,
            0x0c, 1, ord('k'),
            OpCode.HASKEY,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True


class TestStructOperations:
    """Test struct operations."""
    
    def test_newstruct0(self):
        """Test NEWSTRUCT0 creates empty struct."""
        script = bytes([OpCode.NEWSTRUCT0])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert isinstance(result, Struct)
        assert len(result) == 0
    
    def test_newstruct(self):
        """Test NEWSTRUCT creates struct with size."""
        script = bytes([
            OpCode.PUSH2,
            OpCode.NEWSTRUCT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert isinstance(result, Struct)
        assert len(result) == 2
