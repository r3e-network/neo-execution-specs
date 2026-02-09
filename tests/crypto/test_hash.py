"""Tests for crypto module."""

from neo.crypto.hash import hash160, hash256


class TestHash:
    """Hash tests."""
    
    def test_hash160(self):
        """Test hash160."""
        result = hash160(b"test")
        assert len(result) == 20
    
    def test_hash256(self):
        """Test hash256."""
        result = hash256(b"test")
        assert len(result) == 32
