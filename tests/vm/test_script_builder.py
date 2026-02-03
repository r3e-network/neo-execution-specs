"""Tests for ScriptBuilder."""

import pytest
from neo.vm.script_builder import ScriptBuilder


def test_emit():
    """Test emit."""
    sb = ScriptBuilder()
    sb.emit(0x10)
    assert sb.to_bytes() == bytes([0x10])
