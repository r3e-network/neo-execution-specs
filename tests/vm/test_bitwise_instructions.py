"""Tests for bitwise instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestBitwiseInstructions:
    """Test bitwise operations."""
    
    def test_invert(self):
        """Test INVERT bitwise NOT."""
        script = bytes([
            OpCode.PUSH0,
            OpCode.INVERT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == -1
    
    def test_and(self):
        """Test AND bitwise AND."""
        script = bytes([
            OpCode.PUSH15,  # 0b1111
            OpCode.PUSH10,  # 0b1010
            OpCode.AND,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 10  # 0b1010
    
    def test_or(self):
        """Test OR bitwise OR."""
        script = bytes([
            OpCode.PUSH5,   # 0b0101
            OpCode.PUSH10,  # 0b1010
            OpCode.OR,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 15  # 0b1111
    
    def test_xor(self):
        """Test XOR bitwise XOR."""
        script = bytes([
            OpCode.PUSH15,  # 0b1111
            OpCode.PUSH10,  # 0b1010
            OpCode.XOR,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5  # 0b0101
    
    def test_equal_true(self):
        """Test EQUAL with equal values."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.PUSH5,
            OpCode.EQUAL,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_equal_false(self):
        """Test EQUAL with different values."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.PUSH6,
            OpCode.EQUAL,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == False
    
    def test_notequal(self):
        """Test NOTEQUAL."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.PUSH6,
            OpCode.NOTEQUAL,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
