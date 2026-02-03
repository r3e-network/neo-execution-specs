"""Tests for VM HASKEY instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestHasKeyInstruction:
    """Test HASKEY instruction."""
    
    def test_haskey_array(self):
        """Test HASKEY on array."""
        engine = ExecutionEngine()
        engine.load_script(bytes([
            OpCode.NEWARRAY0, OpCode.PUSH0, OpCode.HASKEY
        ]))
        engine.execute()
        assert len(engine.result_stack) == 1
