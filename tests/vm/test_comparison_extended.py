"""Tests for VM comparison instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode


class TestComparisonInstructions:
    """Comparison instruction tests."""
    
    def test_equal_true(self):
        """Test EQUAL with equal values."""
        sb = ScriptBuilder()
        sb.emit_push(5)
        sb.emit_push(5)
        sb.emit(OpCode.EQUAL)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_boolean() is True
    
    def test_equal_false(self):
        """Test EQUAL with different values."""
        sb = ScriptBuilder()
        sb.emit_push(5)
        sb.emit_push(3)
        sb.emit(OpCode.EQUAL)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_boolean() is False
    
    def test_lt(self):
        """Test LT instruction."""
        sb = ScriptBuilder()
        sb.emit_push(3)
        sb.emit_push(5)
        sb.emit(OpCode.LT)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_boolean() is True
    
    def test_gt(self):
        """Test GT instruction."""
        sb = ScriptBuilder()
        sb.emit_push(10)
        sb.emit_push(5)
        sb.emit(OpCode.GT)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_boolean() is True
