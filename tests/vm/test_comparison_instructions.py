"""Tests for numeric comparison instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestComparisonInstructions:
    """Test numeric comparison operations."""
    
    def test_lt_true(self):
        """Test LT with less than."""
        script = bytes([OpCode.PUSH3, OpCode.PUSH5, OpCode.LT])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_lt_false(self):
        """Test LT with not less than."""
        script = bytes([OpCode.PUSH5, OpCode.PUSH3, OpCode.LT])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == False
    
    def test_le(self):
        """Test LE (less than or equal)."""
        script = bytes([OpCode.PUSH5, OpCode.PUSH5, OpCode.LE])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_gt(self):
        """Test GT (greater than)."""
        script = bytes([OpCode.PUSH5, OpCode.PUSH3, OpCode.GT])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_ge(self):
        """Test GE (greater than or equal)."""
        script = bytes([OpCode.PUSH5, OpCode.PUSH5, OpCode.GE])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_min(self):
        """Test MIN returns smaller value."""
        script = bytes([OpCode.PUSH3, OpCode.PUSH7, OpCode.MIN])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 3
    
    def test_max(self):
        """Test MAX returns larger value."""
        script = bytes([OpCode.PUSH3, OpCode.PUSH7, OpCode.MAX])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 7
