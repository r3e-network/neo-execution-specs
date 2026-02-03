"""Tests for VM SETITEM instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestSetItemInstruction:
    """Test SETITEM instruction."""
    
    def test_setitem_array(self):
        """Test SETITEM on array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH0, OpCode.PUSH1, OpCode.PACK,
            OpCode.PUSH0, OpCode.PUSH5, OpCode.SETITEM
        ]))
        engine.execute()
        assert len(engine.result_stack) == 0
