"""Tests for VM stack instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode


class TestStackInstructions:
    """Stack instruction tests."""
    
    def test_dup(self):
        """Test DUP instruction."""
        sb = ScriptBuilder()
        sb.emit_push(42)
        sb.emit(OpCode.DUP)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 42
        assert engine.result_stack.pop().get_integer() == 42
    
    def test_drop(self):
        """Test DROP instruction."""
        sb = ScriptBuilder()
        sb.emit_push(1)
        sb.emit_push(2)
        sb.emit(OpCode.DROP)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 1
    
    def test_swap(self):
        """Test SWAP instruction."""
        sb = ScriptBuilder()
        sb.emit_push(1)
        sb.emit_push(2)
        sb.emit(OpCode.SWAP)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.pop().get_integer() == 1
        assert engine.result_stack.pop().get_integer() == 2
