"""Tests for VM REMOVE instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestRemoveInstruction:
    """Test REMOVE instruction."""
    
    def test_remove_array(self):
        """Test REMOVE from array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH1, OpCode.PACK,
            OpCode.PUSH0, OpCode.REMOVE
        ]))
        engine.execute()
        assert len(engine.result_stack) == 0
