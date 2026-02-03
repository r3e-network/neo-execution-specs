"""Tests for increment/decrement instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestIncDecInstructions:
    """Test increment/decrement operations."""
    
    def test_inc(self):
        """Test INC (increment)."""
        script = bytes([OpCode.PUSH5, OpCode.INC])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 6
    
    def test_dec(self):
        """Test DEC (decrement)."""
        script = bytes([OpCode.PUSH5, OpCode.DEC])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 4
