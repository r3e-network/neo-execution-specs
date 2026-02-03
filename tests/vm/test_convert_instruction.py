"""Tests for VM CONVERT instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestConvertInstruction:
    """Test CONVERT instruction."""
    
    def test_convert_to_int(self):
        """Test CONVERT to integer."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.PUSH1, OpCode.CONVERT, 0x21]))
        engine.execute()
        assert len(engine.result_stack) == 1
