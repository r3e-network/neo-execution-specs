"""Tests for VM PICKITEM instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestPickItemInstruction:
    """Test PICKITEM instruction."""
    
    def test_pickitem_array(self):
        """Test PICKITEM on array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH1, OpCode.PACK,
            OpCode.PUSH0, OpCode.PICKITEM
        ]))
        engine.execute()
        assert engine.result_stack.pop().get_integer() == 1
