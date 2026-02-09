"""Tests for VM RET instruction."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestRetInstruction:
    """Test RET instruction."""
    
    def test_ret(self):
        """Test RET ends execution."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.RET]))
        engine.execute()
        assert engine.state == VMState.HALT
