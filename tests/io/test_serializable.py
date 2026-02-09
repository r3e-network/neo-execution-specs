"""Tests for Serializable."""

from neo.io.serializable import ISerializable


class TestSerializable:
    """Test ISerializable."""
    
    def test_interface(self):
        """Test interface exists."""
        assert ISerializable is not None
