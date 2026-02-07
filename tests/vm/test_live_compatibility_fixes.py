"""Targeted compatibility regression tests from live Neo v3.9.1 diffs."""

from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


def test_jump_out_of_script_faults_when_target_equals_length():
    """Neo faults when jump target points exactly past script end."""
    # PUSH1; JMP +3; PUSH2  (jump target resolves to position 4 == len(script))
    script = bytes([OpCode.PUSH1, OpCode.JMP, 3, OpCode.PUSH2])
    engine = ExecutionEngine()
    engine.load_script(script)
    engine.execute()
    assert engine.state == VMState.FAULT


def test_splice_cat_returns_buffer_type():
    """CAT should produce Buffer for parity with current vector expectations."""
    script = bytes([
        OpCode.PUSHDATA1, 2, 0x01, 0x02,
        OpCode.PUSHDATA1, 2, 0x03, 0x04,
        OpCode.CAT,
    ])
    engine = ExecutionEngine()
    engine.load_script(script)
    engine.execute()

    assert engine.state == VMState.HALT
    result = engine.result_stack.peek()
    assert result.type.name == "BUFFER"
    assert result.get_bytes_unsafe().hex() == "01020304"


def test_splice_newbuffer_zeroed_bytes():
    """NEWBUFFER should initialize with zero bytes."""
    script = bytes([OpCode.PUSH4, OpCode.NEWBUFFER])
    engine = ExecutionEngine()
    engine.load_script(script)
    engine.execute()

    assert engine.state == VMState.HALT
    result = engine.result_stack.peek()
    assert result.type.name == "BUFFER"
    assert result.get_bytes_unsafe().hex() == "00000000"

