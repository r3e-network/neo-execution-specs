"""Tests for VM NEWMAP instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestNewMapInstruction:
    """Test NEWMAP instruction."""
    
    def test_newmap(self):
        """Test NEWMAP."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.NEWMAP]))
        engine.execute()
        assert len(engine.result_stack) == 1
