"""Tests for stack instructions."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestStackInstructions:
    """Test stack manipulation operations."""
    
    def test_depth(self):
        """Test DEPTH returns stack size."""
        script = bytes([
            OpCode.PUSH1,
            OpCode.PUSH2,
            OpCode.PUSH3,
            OpCode.DEPTH,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 3
    
    def test_drop(self):
        """Test DROP removes top item."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.PUSH3,
            OpCode.DROP,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5
    
    def test_dup(self):
        """Test DUP duplicates top item."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.DUP,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert len(engine.result_stack) == 2
        assert engine.result_stack.peek(0).get_integer() == 5
        assert engine.result_stack.peek(1).get_integer() == 5
    
    def test_swap(self):
        """Test SWAP exchanges top two items."""
        script = bytes([
            OpCode.PUSH1,
            OpCode.PUSH2,
            OpCode.SWAP,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek(0).get_integer() == 1
        assert engine.result_stack.peek(1).get_integer() == 2
    
    def test_rot(self):
        """Test ROT rotates top 3 items."""
        script = bytes([
            OpCode.PUSH1,
            OpCode.PUSH2,
            OpCode.PUSH3,
            OpCode.ROT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        # After ROT: [2, 3, 1] -> top is 2
        assert engine.result_stack.peek(0).get_integer() == 1
