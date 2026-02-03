"""Tests for MODMUL and MODPOW instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestModMulInstruction:
    """Test MODMUL instruction."""
    
    def test_modmul_basic(self):
        """Test (3 * 4) % 5 = 2."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH3, OpCode.PUSH4, OpCode.PUSH5, OpCode.MODMUL
        ]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 2


class TestModPowInstruction:
    """Test MODPOW instruction."""
    
    def test_modpow_basic(self):
        """Test (2^3) % 5 = 3."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH2, OpCode.PUSH3, OpCode.PUSH5, OpCode.MODPOW
        ]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 3
