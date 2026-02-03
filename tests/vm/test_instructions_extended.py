"""Additional tests for VM instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestNumericInstructions:
    """Tests for numeric VM instructions."""
    
    def test_add(self):
        """Test ADD instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH10, OpCode.PUSH5, OpCode.ADD])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_sub(self):
        """Test SUB instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH10, OpCode.PUSH3, OpCode.SUB])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_mul(self):
        """Test MUL instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.PUSH6, OpCode.MUL])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_div(self):
        """Test DIV instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH8, OpCode.PUSH2, OpCode.DIV])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_mod(self):
        """Test MOD instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH10, OpCode.PUSH3, OpCode.MOD])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_negate(self):
        """Test NEGATE instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.NEGATE])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_abs(self):
        """Test ABS instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSHM1, OpCode.ABS])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_inc(self):
        """Test INC instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.INC])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
    
    def test_dec(self):
        """Test DEC instruction."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.DEC])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
