"""Tests for VM CLEARITEMS instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestClearItemsInstruction:
    """Test CLEARITEMS instruction."""
    
    def test_clearitems(self):
        """Test CLEARITEMS on array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH1, OpCode.PACK,
            OpCode.CLEARITEMS
        ]))
        engine.execute()
        assert len(engine.result_stack) == 0
