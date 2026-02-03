"""Tests for CryptoLib native contract."""

import pytest
from neo.native.crypto_lib import CryptoLib, NamedCurveHash


class TestCryptoLibHash:
    """Tests for CryptoLib hash functions."""
    
    def setup_method(self):
        self.crypto = CryptoLib()
    
    def test_sha256(self):
        """Test SHA256 hash."""
        result = self.crypto.sha256(b"hello")
        assert len(result) == 32
        # Known SHA256 of "hello"
        expected = bytes.fromhex(
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        )
        assert result == expected
    
    def test_sha256_empty(self):
        """Test SHA256 of empty input."""
        result = self.crypto.sha256(b"")
        assert len(result) == 32
    
    def test_ripemd160(self):
        """Test RIPEMD160 hash."""
        result = self.crypto.ripemd160(b"hello")
        assert len(result) == 20
    
    def test_murmur32(self):
        """Test Murmur32 hash."""
        result = self.crypto.murmur32(b"hello", 0)
        assert len(result) == 4


class TestNamedCurveHash:
    """Tests for NamedCurveHash enum."""
    
    def test_secp256k1_sha256(self):
        """Test secp256k1 with SHA256."""
        assert NamedCurveHash.secp256k1SHA256 == 22
    
    def test_secp256r1_sha256(self):
        """Test secp256r1 with SHA256."""
        assert NamedCurveHash.secp256r1SHA256 == 23
    
    def test_secp256k1_keccak256(self):
        """Test secp256k1 with Keccak256."""
        assert NamedCurveHash.secp256k1Keccak256 == 24
    
    def test_secp256r1_keccak256(self):
        """Test secp256r1 with Keccak256."""
        assert NamedCurveHash.secp256r1Keccak256 == 25
