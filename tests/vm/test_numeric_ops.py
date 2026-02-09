"""Tests for numeric operations."""

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


def test_shl_shift_zero():
    """Test SHL with shift=0 preserves stack correctly.
    
    This tests the fix for the stack corruption bug where shift=0
    would return early without pushing the value back.
    """
    engine = ExecutionEngine()
    # PUSH 42, PUSH0 (shift=0), SHL
    script = bytes([OpCode.PUSHINT8, 42, OpCode.PUSH0, OpCode.SHL])
    engine.load_script(script)
    engine.execute()
    assert engine.state == VMState.HALT
    # Stack should have exactly one item: 42
    result = engine.result_stack
    assert len(result) == 1
    assert result.peek(0).get_integer() == 42


def test_shr_shift_zero():
    """Test SHR with shift=0 preserves stack correctly.
    
    This tests the fix for the stack corruption bug where shift=0
    would return early without pushing the value back.
    """
    engine = ExecutionEngine()
    # PUSH 42, PUSH0 (shift=0), SHR
    script = bytes([OpCode.PUSHINT8, 42, OpCode.PUSH0, OpCode.SHR])
    engine.load_script(script)
    engine.execute()
    assert engine.state == VMState.HALT
    # Stack should have exactly one item: 42
    result = engine.result_stack
    assert len(result) == 1
    assert result.peek(0).get_integer() == 42


def test_shl_normal():
    """Test SHL with non-zero shift."""
    engine = ExecutionEngine()
    # PUSH 1, PUSH 4, SHL -> 1 << 4 = 16
    script = bytes([OpCode.PUSH1, OpCode.PUSH4, OpCode.SHL])
    engine.load_script(script)
    engine.execute()
    assert engine.state == VMState.HALT
    result = engine.result_stack
    assert len(result) == 1
    assert result.peek(0).get_integer() == 16


def test_shr_normal():
    """Test SHR with non-zero shift."""
    engine = ExecutionEngine()
    # PUSH 16, PUSH 2, SHR -> 16 >> 2 = 4
    script = bytes([OpCode.PUSHINT8, 16, OpCode.PUSH2, OpCode.SHR])
    engine.load_script(script)
    engine.execute()
    assert engine.state == VMState.HALT
    result = engine.result_stack
    assert len(result) == 1
    assert result.peek(0).get_integer() == 4
