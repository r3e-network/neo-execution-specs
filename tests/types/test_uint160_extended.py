"""Tests for UInt160."""

import pytest
from neo.types.uint160 import UInt160


class TestUInt160Extended:
    """Extended UInt160 tests."""
    
    def test_zero(self):
        """Test zero value."""
        u = UInt160()
        assert u.data == bytes(20)
    
    def test_from_bytes(self):
        """Test from bytes."""
        data = bytes(range(20))
        u = UInt160(data)
        assert u.data == data
