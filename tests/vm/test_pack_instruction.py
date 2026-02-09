"""Tests for VM PACK instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestPackInstruction:
    """Test PACK instruction."""
    
    def test_pack(self):
        """Test PACK."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH2, OpCode.PUSH2, OpCode.PACK
        ]))
        engine.execute()
        assert len(engine.result_stack) == 1
