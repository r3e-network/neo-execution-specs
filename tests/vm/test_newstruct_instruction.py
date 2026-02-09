"""Tests for VM NEWSTRUCT instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestNewStructInstruction:
    """Test NEWSTRUCT instruction."""
    
    def test_newstruct0(self):
        """Test NEWSTRUCT0."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.NEWSTRUCT0]))
        engine.execute()
        assert len(engine.result_stack) == 1
