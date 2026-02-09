"""Tests for WITHIN instruction."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestWithinInstruction:
    """Test WITHIN operation."""
    
    def test_within_true(self):
        """Test WITHIN when value is in range."""
        # WITHIN: x a b -> (a <= x < b)
        script = bytes([
            OpCode.PUSH5,   # x = 5
            OpCode.PUSH3,   # a = 3
            OpCode.PUSH8,   # b = 8
            OpCode.WITHIN,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean()
    
    def test_within_false(self):
        """Test WITHIN when value is out of range."""
        script = bytes([
            OpCode.PUSH10,  # x = 10
            OpCode.PUSH3,   # a = 3
            OpCode.PUSH8,   # b = 8
            OpCode.WITHIN,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert not engine.result_stack.peek().get_boolean()
