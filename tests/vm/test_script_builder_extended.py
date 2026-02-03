"""Tests for script builder."""

import pytest
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode


class TestScriptBuilder:
    """Script builder tests."""
    
    def test_emit_push_int(self):
        """Test pushing integer."""
        sb = ScriptBuilder()
        sb.emit_push(42)
        script = sb.to_bytes()
        assert len(script) > 0
    
    def test_emit_push_bytes(self):
        """Test pushing bytes."""
        sb = ScriptBuilder()
        sb.emit_push(b"hello")
        script = sb.to_bytes()
        assert len(script) > 0
    
    def test_emit_opcode(self):
        """Test emitting opcode."""
        sb = ScriptBuilder()
        sb.emit(OpCode.NOP)
        script = sb.to_bytes()
        assert script == bytes([OpCode.NOP])
    
    def test_chain_calls(self):
        """Test chaining calls."""
        sb = ScriptBuilder()
        sb.emit_push(1).emit_push(2).emit(OpCode.ADD)
        script = sb.to_bytes()
        assert len(script) > 0
