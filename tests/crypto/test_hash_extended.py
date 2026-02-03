"""Tests for crypto hash functions."""

import pytest
from neo.crypto.hash import sha256, hash160, hash256


class TestCryptoHash:
    """Test crypto hash functions."""
    
    def test_sha256(self):
        """Test SHA256."""
        result = sha256(b"hello")
        assert len(result) == 32
    
    def test_hash160(self):
        """Test HASH160."""
        result = hash160(b"hello")
        assert len(result) == 20
    
    def test_hash256(self):
        """Test HASH256."""
        result = hash256(b"hello")
        assert len(result) == 32
