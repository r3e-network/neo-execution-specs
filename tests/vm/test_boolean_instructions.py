"""Tests for boolean instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestBooleanInstructions:
    """Test boolean operations."""
    
    def test_not_true(self):
        """Test NOT on true."""
        script = bytes([OpCode.PUSHT, OpCode.NOT])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == False
    
    def test_not_false(self):
        """Test NOT on false."""
        script = bytes([OpCode.PUSHF, OpCode.NOT])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_booland(self):
        """Test BOOLAND."""
        script = bytes([OpCode.PUSHT, OpCode.PUSHT, OpCode.BOOLAND])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_boolor(self):
        """Test BOOLOR."""
        script = bytes([OpCode.PUSHF, OpCode.PUSHT, OpCode.BOOLOR])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_nz(self):
        """Test NZ (not zero)."""
        script = bytes([OpCode.PUSH5, OpCode.NZ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
