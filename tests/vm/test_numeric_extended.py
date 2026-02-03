"""Tests for VM numeric instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode


class TestNumericInstructions:
    """Numeric instruction tests."""
    
    def test_add(self):
        """Test ADD instruction."""
        sb = ScriptBuilder()
        sb.emit_push(5)
        sb.emit_push(3)
        sb.emit(OpCode.ADD)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 8
    
    def test_sub(self):
        """Test SUB instruction."""
        sb = ScriptBuilder()
        sb.emit_push(10)
        sb.emit_push(3)
        sb.emit(OpCode.SUB)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 7
    
    def test_mul(self):
        """Test MUL instruction."""
        sb = ScriptBuilder()
        sb.emit_push(4)
        sb.emit_push(5)
        sb.emit(OpCode.MUL)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 20
    
    def test_div(self):
        """Test DIV instruction."""
        sb = ScriptBuilder()
        sb.emit_push(20)
        sb.emit_push(4)
        sb.emit(OpCode.DIV)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 5
    
    def test_mod(self):
        """Test MOD instruction."""
        sb = ScriptBuilder()
        sb.emit_push(17)
        sb.emit_push(5)
        sb.emit(OpCode.MOD)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 2
    
    def test_negate(self):
        """Test NEGATE instruction."""
        sb = ScriptBuilder()
        sb.emit_push(5)
        sb.emit(OpCode.NEGATE)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == -5
    
    def test_abs(self):
        """Test ABS instruction."""
        sb = ScriptBuilder()
        sb.emit_push(-10)
        sb.emit(OpCode.ABS)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 10
