"""Tests for Base58 encoding/decoding."""

import pytest
from neo.crypto.base58 import encode, decode, base58_check_encode, base58_check_decode


class TestBase58Encode:
    """Tests for Base58 encoding."""
    
    def test_encode_empty(self):
        """Test encoding empty bytes."""
        assert encode(b"") == ""
    
    def test_encode_zeros(self):
        """Test encoding leading zeros."""
        assert encode(b"\x00") == "1"
        assert encode(b"\x00\x00") == "11"
        assert encode(b"\x00\x00\x00") == "111"
    
    def test_encode_hello(self):
        """Test encoding 'hello'."""
        result = encode(b"hello")
        assert result == "Cn8eVZg"
    
    def test_encode_hello_world(self):
        """Test encoding 'Hello World'."""
        result = encode(b"Hello World")
        assert result == "JxF12TrwUP45BMd"
    
    def test_encode_with_leading_zero(self):
        """Test encoding with leading zero byte."""
        result = encode(b"\x00hello")
        assert result.startswith("1")


class TestBase58Decode:
    """Tests for Base58 decoding."""
    
    def test_decode_empty(self):
        """Test decoding empty string."""
        assert decode("") == b""
    
    def test_decode_ones(self):
        """Test decoding leading '1's (zeros)."""
        assert decode("1") == b"\x00"
        assert decode("11") == b"\x00\x00"
    
    def test_decode_hello(self):
        """Test decoding to 'hello'."""
        result = decode("Cn8eVZg")
        assert result == b"hello"
    
    def test_roundtrip(self):
        """Test encode/decode roundtrip."""
        test_data = [
            b"",
            b"\x00",
            b"hello",
            b"Hello World",
            b"\x00\x00test",
            bytes(range(256)),
        ]
        for data in test_data:
            assert decode(encode(data)) == data


class TestBase58Check:
    """Tests for Base58Check encoding/decoding."""
    
    def test_check_encode_decode_roundtrip(self):
        """Test Base58Check roundtrip."""
        data = b"test data"
        encoded = base58_check_encode(data)
        decoded = base58_check_decode(encoded)
        assert decoded == data
    
    def test_check_decode_invalid_checksum(self):
        """Test Base58Check with invalid checksum."""
        # Encode valid data
        encoded = base58_check_encode(b"test")
        # Corrupt the last character
        corrupted = encoded[:-1] + ("2" if encoded[-1] != "2" else "3")
        with pytest.raises(ValueError, match="Invalid checksum"):
            base58_check_decode(corrupted)
    
    def test_check_encode_empty(self):
        """Test Base58Check with empty data."""
        encoded = base58_check_encode(b"")
        decoded = base58_check_decode(encoded)
        assert decoded == b""
