"""Tests for splice instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestSpliceInstructions:
    """Test splice/string operations."""
    
    def test_cat(self):
        """Test CAT concatenates two byte strings."""
        script = bytes([
            0x0c, 2, ord('a'), ord('b'),  # PUSHDATA1 "ab"
            0x0c, 2, ord('c'), ord('d'),  # PUSHDATA1 "cd"
            OpCode.CAT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "abcd"
    
    def test_substr(self):
        """Test SUBSTR extracts substring."""
        script = bytes([
            0x0c, 5, ord('h'), ord('e'), ord('l'), ord('l'), ord('o'),
            OpCode.PUSH1,  # index
            OpCode.PUSH3,  # count
            OpCode.SUBSTR,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "ell"
    
    def test_left(self):
        """Test LEFT extracts left portion."""
        script = bytes([
            0x0c, 5, ord('h'), ord('e'), ord('l'), ord('l'), ord('o'),
            OpCode.PUSH2,  # count
            OpCode.LEFT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "he"
    
    def test_right(self):
        """Test RIGHT extracts right portion."""
        script = bytes([
            0x0c, 5, ord('h'), ord('e'), ord('l'), ord('l'), ord('o'),
            OpCode.PUSH2,  # count
            OpCode.RIGHT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "lo"
    
    def test_newbuffer(self):
        """Test NEWBUFFER creates buffer."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.NEWBUFFER,
            OpCode.SIZE,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5
