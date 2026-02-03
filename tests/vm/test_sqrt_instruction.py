"""Tests for SQRT instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestSqrtInstruction:
    """Test SQRT instruction."""
    
    def test_sqrt_4(self):
        """Test sqrt(4) = 2."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.PUSH4, OpCode.SQRT]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 2
    
    def test_sqrt_9(self):
        """Test sqrt(9) = 3."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.PUSH9, OpCode.SQRT]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 3
    
    def test_sqrt_0(self):
        """Test sqrt(0) = 0."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.PUSH0, OpCode.SQRT]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 0
