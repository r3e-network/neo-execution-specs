"""Tests for VM REVERSEITEMS instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestReverseItemsInstruction:
    """Test REVERSEITEMS instruction."""
    
    def test_reverseitems(self):
        """Test REVERSEITEMS on array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH2, OpCode.PUSH2, OpCode.PACK,
            OpCode.REVERSEITEMS
        ]))
        engine.execute()
        assert len(engine.result_stack) == 0
