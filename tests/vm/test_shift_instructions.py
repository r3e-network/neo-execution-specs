"""Tests for shift instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestShiftInstructions:
    """Test bit shift operations."""
    
    def test_shl(self):
        """Test SHL (shift left)."""
        script = bytes([OpCode.PUSH1, OpCode.PUSH3, OpCode.SHL])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 8
    
    def test_shr(self):
        """Test SHR (shift right)."""
        script = bytes([OpCode.PUSH16, OpCode.PUSH2, OpCode.SHR])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 4
