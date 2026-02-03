"""Tests for opcode definitions."""

import pytest
from neo.vm.opcode import OpCode


class TestOpCode:
    """Opcode tests."""
    
    def test_push0(self):
        """Test PUSH0 value."""
        assert OpCode.PUSH0 == 0x10
    
    def test_push1(self):
        """Test PUSH1 value."""
        assert OpCode.PUSH1 == 0x11
    
    def test_nop(self):
        """Test NOP value."""
        assert OpCode.NOP == 0x21
    
    def test_ret(self):
        """Test RET value."""
        assert OpCode.RET == 0x40
