"""Tests for VM APPEND instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestAppendInstruction:
    """Test APPEND instruction."""
    
    def test_append(self):
        """Test APPEND to array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.NEWARRAY0, OpCode.DUP,
            OpCode.PUSH1, OpCode.APPEND
        ]))
        engine.execute()
        assert len(engine.result_stack) == 1
