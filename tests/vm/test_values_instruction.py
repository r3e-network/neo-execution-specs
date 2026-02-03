"""Tests for VM VALUES instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestValuesInstruction:
    """Test VALUES instruction."""
    
    def test_values(self):
        """Test VALUES on map."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.NEWMAP, OpCode.VALUES]))
        engine.execute()
        assert len(engine.result_stack) == 1
