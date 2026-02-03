"""Tests for VM NEWBUFFER instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestNewBufferInstruction:
    """Test NEWBUFFER instruction."""
    
    def test_newbuffer(self):
        """Test NEWBUFFER."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.PUSH5, OpCode.NEWBUFFER]))
        engine.execute()
        assert len(engine.result_stack) == 1
