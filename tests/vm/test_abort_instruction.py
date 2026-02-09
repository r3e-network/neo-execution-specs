"""Tests for VM ABORT instruction."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestAbortInstruction:
    """Test ABORT instruction."""
    
    def test_abort(self):
        """Test ABORT halts execution."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.ABORT]))
        engine.execute()
        assert engine.state == VMState.FAULT
