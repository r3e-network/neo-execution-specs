"""Tests for KeyPair."""

import pytest
from neo.wallets.key_pair import (
    KeyPair,
    base58_encode,
    base58_decode,
    base58_check_encode,
    base58_check_decode,
)


class TestBase58:
    """Tests for Base58 encoding/decoding."""
    
    def test_encode_empty(self):
        """Test encoding empty bytes."""
        assert base58_encode(b"") == "1"
    
    def test_encode_zero(self):
        """Test encoding zero byte."""
        assert base58_encode(b"\x00") == "1"
    
    def test_encode_basic(self):
        """Test basic encoding."""
        result = base58_encode(b"Hello")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_decode_one(self):
        """Test decoding '1'."""
        assert base58_decode("1") == b"\x00"
    
    def test_round_trip(self):
        """Test encode/decode round trip."""
        data = b"Hello, Neo!"
        encoded = base58_encode(data)
        decoded = base58_decode(encoded)
        assert decoded == data
    
    def test_leading_zeros(self):
        """Test handling of leading zeros."""
        data = b"\x00\x00\x00test"
        encoded = base58_encode(data)
        decoded = base58_decode(encoded)
        assert decoded == data


class TestBase58Check:
    """Tests for Base58Check encoding/decoding."""
    
    def test_encode_basic(self):
        """Test basic check encoding."""
        data = b"test"
        encoded = base58_check_encode(data)
        assert isinstance(encoded, str)
    
    def test_round_trip(self):
        """Test encode/decode round trip."""
        data = b"Hello, Neo!"
        encoded = base58_check_encode(data)
        decoded = base58_check_decode(encoded)
        assert decoded == data
    
    def test_invalid_checksum(self):
        """Test invalid checksum detection."""
        data = b"test"
        encoded = base58_check_encode(data)
        # Corrupt the encoded string
        corrupted = encoded[:-1] + ("2" if encoded[-1] != "2" else "3")
        with pytest.raises(ValueError, match="Invalid checksum"):
            base58_check_decode(corrupted)


class TestKeyPair:
    """Tests for KeyPair class."""
    
    def test_invalid_private_key_length(self):
        """Test that invalid private key length raises error."""
        with pytest.raises(ValueError, match="32 bytes"):
            KeyPair(private_key=b"short", public_key=None)
