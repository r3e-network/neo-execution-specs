"""Tests for slot instructions."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestSlotInstructions:
    """Test slot operations for local variables and arguments."""
    
    def test_initslot(self):
        """Test INITSLOT initializes local and argument slots."""
        script = bytes([
            OpCode.INITSLOT,
            2,  # 2 locals
            0,  # 0 arguments (no args needed)
            OpCode.PUSH5,
            OpCode.STLOC0,
            OpCode.LDLOC0,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5
    
    def test_ldloc_stloc(self):
        """Test LDLOC and STLOC operations."""
        script = bytes([
            OpCode.INITSLOT, 3, 0,
            OpCode.PUSH5,
            OpCode.STLOC0,
            OpCode.PUSH7,
            OpCode.STLOC1,
            OpCode.LDLOC0,
            OpCode.LDLOC1,
            OpCode.ADD,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 12
    
    def test_initsslot(self):
        """Test INITSSLOT initializes static slots."""
        script = bytes([
            OpCode.INITSSLOT, 2,
            OpCode.PUSH7,
            OpCode.STSFLD0,
            OpCode.LDSFLD0,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 7
