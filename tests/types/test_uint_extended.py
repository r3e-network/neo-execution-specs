"""Tests for types module."""

import pytest
from neo.types.uint160 import UInt160
from neo.types.uint256 import UInt256


class TestUInt160Extended:
    """Extended UInt160 tests."""
    
    def test_from_bytes(self):
        """Test creation from bytes."""
        data = b"\x01" * 20
        u = UInt160(data)
        assert bytes(u) == data
    
    def test_zero(self):
        """Test zero value."""
        u = UInt160(b"\x00" * 20)
        assert bytes(u) == b"\x00" * 20
    
    def test_equality(self):
        """Test equality."""
        u1 = UInt160(b"\x01" * 20)
        u2 = UInt160(b"\x01" * 20)
        assert u1 == u2


class TestUInt256Extended:
    """Extended UInt256 tests."""
    
    def test_from_bytes(self):
        """Test creation from bytes."""
        data = b"\x01" * 32
        u = UInt256(data)
        assert bytes(u) == data
    
    def test_zero(self):
        """Test zero value."""
        u = UInt256(b"\x00" * 32)
        assert bytes(u) == b"\x00" * 32
