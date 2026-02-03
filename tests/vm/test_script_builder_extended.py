"""Tests for ScriptBuilder."""

import pytest
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode


class TestScriptBuilderExtended:
    """Test ScriptBuilder."""
    
    def test_emit_push_int(self):
        """Test emit_push with integer."""
        sb = ScriptBuilder()
        sb.emit_push(5)
        assert len(sb.to_bytes()) > 0
