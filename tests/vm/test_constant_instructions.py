"""Tests for constant instructions."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestPushInstructions:
    """Test push constant operations."""
    
    def test_push0_to_push16(self):
        """Test PUSH0 through PUSH16."""
        for i in range(17):
            script = bytes([OpCode.PUSH0 + i])
            engine = ExecutionEngine()
            engine.load_script(script)
            engine.execute()
            
            assert engine.state == VMState.HALT
            assert engine.result_stack.peek().get_integer() == i
    
    def test_pushm1(self):
        """Test PUSHM1 pushes -1."""
        script = bytes([OpCode.PUSHM1])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == -1
    
    def test_pusht(self):
        """Test PUSHT pushes true."""
        script = bytes([OpCode.PUSHT])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean()
    
    def test_pushf(self):
        """Test PUSHF pushes false."""
        script = bytes([OpCode.PUSHF])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert not engine.result_stack.peek().get_boolean()
    
    def test_pushnull(self):
        """Test PUSHNULL pushes null."""
        script = bytes([OpCode.PUSHNULL])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        from neo.vm.types import Null
        assert isinstance(engine.result_stack.peek(), Null)
