"""Tests for VM stack operations."""

import pytest
from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


def test_push0():
    """Test PUSH0 opcode."""
    engine = ExecutionEngine()
    engine.load_script(bytes([OpCode.PUSH0]))
    engine.execute()
    
    assert engine.state == VMState.HALT
    ctx = engine.invocation_stack[0] if engine.invocation_stack else None
    # Stack should have one item


def test_push_numbers():
    """Test PUSH1-PUSH16."""
    for i in range(1, 17):
        engine = ExecutionEngine()
        opcode = OpCode.PUSH0 + i
        engine.load_script(bytes([opcode]))
        engine.execute()
        assert engine.state == VMState.HALT
