"""Tests for ScriptBuilder."""

import pytest
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode


def test_emit_push():
    """Test pushing integers."""
    sb = ScriptBuilder()
    sb.emit_push(0).emit_push(1).emit_push(16)
    script = sb.to_bytes()
    assert script[0] == OpCode.PUSH0
    assert script[1] == OpCode.PUSH1
    assert script[2] == OpCode.PUSH16
