"""Tests for control flow instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestJumpInstructions:
    """Test jump operations."""
    
    def test_jmp(self):
        """Test unconditional JMP."""
        script = bytes([
            OpCode.JMP, 3,      # Jump +3 (skip PUSH1)
            OpCode.PUSH1,       # Skipped
            OpCode.PUSH5,       # Landed here
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5
    
    def test_jmpif_true(self):
        """Test JMPIF with true condition."""
        script = bytes([
            OpCode.PUSHT,
            OpCode.JMPIF, 3,
            OpCode.PUSH1,
            OpCode.PUSH5,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5
    
    def test_jmpif_false(self):
        """Test JMPIF with false condition."""
        script = bytes([
            OpCode.PUSHF,
            OpCode.JMPIF, 3,
            OpCode.PUSH1,
            OpCode.PUSH5,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        # Both PUSH1 and PUSH5 executed
        assert len(engine.result_stack) == 2


class TestCallInstructions:
    """Test call operations."""
    
    def test_call_and_ret(self):
        """Test CALL and RET."""
        script = bytes([
            OpCode.CALL, 4,     # Call +4
            OpCode.PUSH1,       # After return
            OpCode.JMP, 4,      # Skip function
            OpCode.PUSH5,       # Function body
            OpCode.RET,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        # Function returns 5, then PUSH1
        assert len(engine.result_stack) == 2


class TestNopInstruction:
    """Test NOP instruction."""
    
    def test_nop(self):
        """Test NOP does nothing."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.NOP,
            OpCode.NOP,
            OpCode.NOP,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5
