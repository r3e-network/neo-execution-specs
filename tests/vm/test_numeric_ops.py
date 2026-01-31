"""Tests for numeric operations."""

import pytest
from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


def test_add():
    """Test ADD opcode."""
    engine = ExecutionEngine()
    # PUSH1, PUSH2, ADD
    script = bytes([OpCode.PUSH1, OpCode.PUSH2, OpCode.ADD])
    engine.load_script(script)
    engine.execute()
    assert engine.state == VMState.HALT


def test_sub():
    """Test SUB opcode."""
    engine = ExecutionEngine()
    script = bytes([OpCode.PUSH5, OpCode.PUSH3, OpCode.SUB])
    engine.load_script(script)
    engine.execute()
    assert engine.state == VMState.HALT
