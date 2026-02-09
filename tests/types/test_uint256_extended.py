"""Tests for UInt256."""

from neo.types.uint256 import UInt256


class TestUInt256Extended:
    """Extended UInt256 tests."""
    
    def test_zero(self):
        """Test zero value."""
        u = UInt256()
        assert u.data == bytes(32)
    
    def test_from_bytes(self):
        """Test from bytes."""
        data = bytes(range(32))
        u = UInt256(data)
        assert u.data == data
