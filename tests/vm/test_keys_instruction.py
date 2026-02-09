"""Tests for VM KEYS instruction."""

from neo.vm.execution_engine import ExecutionEngine
from neo.vm.opcode import OpCode


class TestKeysInstruction:
    """Test KEYS instruction."""
    
    def test_keys(self):
        """Test KEYS on map."""
        engine = ExecutionEngine()
        engine.load_script(bytes([OpCode.NEWMAP, OpCode.KEYS]))
        engine.execute()
        assert len(engine.result_stack) == 1
