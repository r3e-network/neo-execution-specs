"""Tests for SIGN instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestSignInstruction:
    """Test SIGN operation."""
    
    def test_sign_positive(self):
        """Test SIGN with positive number."""
        script = bytes([OpCode.PUSH5, OpCode.SIGN])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 1
    
    def test_sign_zero(self):
        """Test SIGN with zero."""
        script = bytes([OpCode.PUSH0, OpCode.SIGN])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 0
    
    def test_sign_negative(self):
        """Test SIGN with negative number."""
        script = bytes([OpCode.PUSH5, OpCode.NEGATE, OpCode.SIGN])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == -1
