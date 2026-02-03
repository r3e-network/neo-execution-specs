"""Tests for execution context."""

import pytest
from neo.vm.execution_context import ExecutionContext


class TestExecutionContext:
    """Tests for ExecutionContext."""
    
    def test_create(self):
        """Test creating execution context."""
        script = bytes([0x10, 0x11, 0x9E])  # PUSH0, PUSH1, ADD
        ctx = ExecutionContext(script=script)
        assert ctx is not None
    
    def test_script(self):
        """Test script property."""
        script = bytes([0x10, 0x11])
        ctx = ExecutionContext(script=script)
        assert ctx.script == script
    
    def test_ip(self):
        """Test instruction pointer."""
        script = bytes([0x10, 0x11])
        ctx = ExecutionContext(script=script)
        assert ctx.ip == 0
