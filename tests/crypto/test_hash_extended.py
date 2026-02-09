"""Tests for crypto module."""

from neo.crypto.hash import hash160, hash256, sha256


class TestHashFunctions:
    """Hash function tests."""
    
    def test_sha256(self):
        """Test SHA256."""
        result = sha256(b"test")
        assert len(result) == 32
    
    def test_hash256(self):
        """Test double SHA256."""
        result = hash256(b"test")
        assert len(result) == 32
    
    def test_hash160(self):
        """Test RIPEMD160(SHA256)."""
        result = hash160(b"test")
        assert len(result) == 20
    
    def test_deterministic(self):
        """Test hash functions are deterministic."""
        data = b"hello world"
        assert hash256(data) == hash256(data)
        assert hash160(data) == hash160(data)
