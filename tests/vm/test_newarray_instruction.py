"""Tests for VM NEWARRAY instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestNewArrayInstruction:
    """Test NEWARRAY instruction."""
    
    def test_newarray0(self):
        """Test NEWARRAY0."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.NEWARRAY0]))
        engine.execute()
        assert len(engine.result_stack) == 1
