"""Tests for VM SIZE instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestSizeInstruction:
    """Test SIZE instruction."""
    
    def test_size_bytes(self):
        """Test SIZE of byte string."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSHDATA1, 3, 0x01, 0x02, 0x03, OpCode.SIZE
        ]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 3
