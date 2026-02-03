"""Tests for execution engine."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode


class TestExecutionEngine:
    """Execution engine tests."""
    
    def test_create_engine(self):
        """Test engine creation."""
        engine = ExecutionEngine()
        assert engine.state == VMState.NONE
    
    def test_load_script(self):
        """Test loading script."""
        engine = ExecutionEngine()
        engine.load_script(b"\x10")
        assert len(engine.invocation_stack) == 1
    
    def test_execute_simple(self):
        """Test simple execution."""
        sb = ScriptBuilder()
        sb.emit_push(42)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
