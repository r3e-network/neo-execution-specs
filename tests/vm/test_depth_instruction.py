"""Tests for VM DEPTH instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestDepthInstruction:
    """Test DEPTH instruction."""
    
    def test_depth_empty(self):
        """Test DEPTH on empty stack."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.DEPTH]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 0
