"""Tests for types module."""

import pytest
from neo.types import UInt160, UInt256


class TestUInt160:
    """UInt160 tests."""
    
    def test_from_string(self):
        """Test from hex string."""
        u = UInt160.from_string("0x" + "ab" * 20)
        assert len(u.data) == 20
    
    def test_str(self):
        """Test string representation."""
        u = UInt160(bytes(20))
        assert str(u).startswith("0x")


class TestUInt256:
    """UInt256 tests."""
    
    def test_from_string(self):
        """Test from hex string."""
        u = UInt256.from_string("0x" + "cd" * 32)
        assert len(u.data) == 32
