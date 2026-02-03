"""Tests for VM CLEAR instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestClearInstruction:
    """Test CLEAR instruction."""
    
    def test_clear(self):
        """Test CLEAR empties stack."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.PUSH1, OpCode.PUSH2, OpCode.CLEAR
        ]))
        engine.execute()
        assert len(engine.result_stack) == 0
