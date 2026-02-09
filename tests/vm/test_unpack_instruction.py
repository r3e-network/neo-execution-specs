"""Tests for VM UNPACK instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestUnpackInstruction:
    """Test UNPACK instruction."""
    
    def test_unpack(self):
        """Test UNPACK."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH1, OpCode.PACK, OpCode.UNPACK
        ]))
        engine.execute()
        assert len(engine.result_stack) == 2
