"""Tests for arithmetic instructions."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestArithmeticInstructions:
    """Test arithmetic operations."""
    
    def test_add(self):
        """Test ADD."""
        script = bytes([OpCode.PUSH3, OpCode.PUSH5, OpCode.ADD])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 8
    
    def test_sub(self):
        """Test SUB."""
        script = bytes([OpCode.PUSH7, OpCode.PUSH3, OpCode.SUB])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 4
    
    def test_mul(self):
        """Test MUL."""
        script = bytes([OpCode.PUSH3, OpCode.PUSH4, OpCode.MUL])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 12
    
    def test_div(self):
        """Test DIV."""
        script = bytes([OpCode.PUSH10, OpCode.PUSH3, OpCode.DIV])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 3
    
    def test_mod(self):
        """Test MOD."""
        script = bytes([OpCode.PUSH10, OpCode.PUSH3, OpCode.MOD])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 1
    
    def test_negate(self):
        """Test NEGATE."""
        script = bytes([OpCode.PUSH5, OpCode.NEGATE])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == -5
    
    def test_abs(self):
        """Test ABS."""
        script = bytes([OpCode.PUSH5, OpCode.NEGATE, OpCode.ABS])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5
