"""Tests for VM NOP instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestNopInstruction:
    """Test NOP instruction."""
    
    def test_nop(self):
        """Test NOP does nothing."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.NOP, OpCode.NOP]))
        engine.execute()
        assert engine.state == VMState.HALT
