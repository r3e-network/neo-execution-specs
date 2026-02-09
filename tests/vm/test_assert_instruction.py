"""Tests for VM ASSERT instruction."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestAssertInstruction:
    """Test ASSERT instruction."""
    
    def test_assert_true(self):
        """Test ASSERT with true."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.PUSHT, OpCode.ASSERT]))
        engine.execute()
        assert engine.state == VMState.HALT
