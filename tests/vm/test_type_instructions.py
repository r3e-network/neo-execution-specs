"""Tests for type instructions."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode
from neo.vm.types import StackItemType


class TestTypeInstructions:
    """Test type checking and conversion operations."""
    
    def test_isnull_true(self):
        """Test ISNULL with null value."""
        script = bytes([
            OpCode.PUSHNULL,
            OpCode.ISNULL,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_isnull_false(self):
        """Test ISNULL with non-null value."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.ISNULL,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == False
    
    def test_istype_integer(self):
        """Test ISTYPE for integer."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.ISTYPE,
            StackItemType.INTEGER,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == True
    
    def test_istype_wrong_type(self):
        """Test ISTYPE with wrong type."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.ISTYPE,
            StackItemType.BYTESTRING,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_boolean() == False
