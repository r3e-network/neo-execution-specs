"""Tests for VM POPITEM instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestPopItemInstruction:
    """Test POPITEM instruction."""
    
    def test_popitem(self):
        """Test POPITEM from array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH1, OpCode.PACK,
            OpCode.POPITEM
        ]))
        engine.execute()
        assert len(engine.result_stack) == 1
