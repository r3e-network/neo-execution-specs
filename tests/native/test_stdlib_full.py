"""Comprehensive tests for StdLib native contract."""

import pytest
from neo.native.std_lib import StdLib


class TestStdLibEncoding:
    """Tests for encoding/decoding functions."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_base64_encode(self):
        """Test base64 encoding."""
        result = self.stdlib.base64_encode(b"hello")
        assert result == "aGVsbG8="
    
    def test_base64_decode(self):
        """Test base64 decoding."""
        result = self.stdlib.base64_decode("aGVsbG8=")
        assert result == b"hello"
    
    def test_base64_roundtrip(self):
        """Test base64 encode/decode roundtrip."""
        data = b"test data 123"
        encoded = self.stdlib.base64_encode(data)
        decoded = self.stdlib.base64_decode(encoded)
        assert decoded == data
    
    def test_base58_encode(self):
        """Test base58 encoding."""
        result = self.stdlib.base58_encode(b"\x00\x00hello")
        assert result.startswith("11")  # Leading zeros become '1's
    
    def test_base58_decode(self):
        """Test base58 decoding."""
        encoded = self.stdlib.base58_encode(b"hello")
        decoded = self.stdlib.base58_decode(encoded)
        assert decoded == b"hello"
    
    def test_base58_check_encode(self):
        """Test base58check encoding."""
        result = self.stdlib.base58_check_encode(b"hello")
        assert len(result) > 0
    
    def test_base58_check_decode(self):
        """Test base58check decoding."""
        encoded = self.stdlib.base58_check_encode(b"hello")
        decoded = self.stdlib.base58_check_decode(encoded)
        assert decoded == b"hello"
    
    def test_base58_check_invalid(self):
        """Test base58check with invalid checksum."""
        with pytest.raises(ValueError):
            self.stdlib.base58_check_decode("invalid")
    
    def test_hex_encode(self):
        """Test hex encoding."""
        result = self.stdlib.hex_encode(b"\xde\xad\xbe\xef")
        assert result == "deadbeef"
    
    def test_hex_decode(self):
        """Test hex decoding."""
        result = self.stdlib.hex_decode("deadbeef")
        assert result == b"\xde\xad\xbe\xef"
    
    def test_base64_url_encode(self):
        """Test base64url encoding."""
        result = self.stdlib.base64_url_encode("hello+world/test")
        assert '+' not in result
        assert '/' not in result
        assert '=' not in result
    
    def test_base64_url_decode(self):
        """Test base64url decoding."""
        encoded = self.stdlib.base64_url_encode("hello")
        decoded = self.stdlib.base64_url_decode(encoded)
        assert decoded == "hello"


class TestStdLibConversion:
    """Tests for conversion functions."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_itoa_decimal(self):
        """Test integer to string (decimal)."""
        assert self.stdlib.itoa(123) == "123"
        assert self.stdlib.itoa(-456) == "-456"
        assert self.stdlib.itoa(0) == "0"
    
    def test_itoa_hex(self):
        """Test integer to string (hex) with Neo/.NET formatting semantics."""
        assert self.stdlib.itoa(255, 16) == "0ff"
        assert self.stdlib.itoa(16, 16) == "10"
        assert self.stdlib.itoa(128, 16) == "080"
    
    def test_atoi_decimal(self):
        """Test string to integer (decimal)."""
        assert self.stdlib.atoi("123") == 123
        assert self.stdlib.atoi("-456") == -456
    
    def test_atoi_hex(self):
        """Test string to integer (hex) using signed interpretation."""
        assert self.stdlib.atoi("ff", 16) == -1
        assert self.stdlib.atoi("10", 16) == 16
    
    def test_atoi_invalid_base(self):
        """Test atoi with invalid base."""
        with pytest.raises(ValueError):
            self.stdlib.atoi("123", 8)


class TestStdLibMemory:
    """Tests for memory functions."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_memory_compare_equal(self):
        """Test memory compare with equal arrays."""
        assert self.stdlib.memory_compare(b"abc", b"abc") == 0
    
    def test_memory_compare_less(self):
        """Test memory compare with less than."""
        assert self.stdlib.memory_compare(b"abc", b"abd") == -1
    
    def test_memory_compare_greater(self):
        """Test memory compare with greater than."""
        assert self.stdlib.memory_compare(b"abd", b"abc") == 1
    
    def test_memory_search_found(self):
        """Test memory search when value is found."""
        assert self.stdlib.memory_search(b"hello world", b"world") == 6
    
    def test_memory_search_not_found(self):
        """Test memory search when value is not found."""
        assert self.stdlib.memory_search(b"hello world", b"xyz") == -1
    
    def test_memory_search_with_start(self):
        """Test memory search with start offset."""
        assert self.stdlib.memory_search(b"hello hello", b"hello", 1) == 6


class TestStdLibString:
    """Tests for string functions."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_string_split(self):
        """Test string split."""
        result = self.stdlib.string_split("a,b,c", ",")
        assert result == ["a", "b", "c"]
    
    def test_string_split_empty(self):
        """Test string split with empty entries."""
        result = self.stdlib.string_split("a,,b", ",")
        assert result == ["a", "", "b"]
    
    def test_string_split_remove_empty(self):
        """Test string split removing empty entries."""
        result = self.stdlib.string_split("a,,b", ",", True)
        assert result == ["a", "b"]
    
    def test_str_len(self):
        """Test string length."""
        assert self.stdlib.str_len("hello") == 5
        assert self.stdlib.str_len("") == 0


class TestStdLibSerialization:
    """Tests for serialization functions."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_serialize_null(self):
        """Test serializing null."""
        result = self.stdlib.serialize(None)
        assert result == bytes([0x00])
    
    def test_serialize_bool_true(self):
        """Test serializing true — type 0x20 (Boolean) + value 0x01."""
        result = self.stdlib.serialize(True)
        assert result == bytes([0x20, 0x01])

    def test_serialize_bool_false(self):
        """Test serializing false — type 0x20 (Boolean) + value 0x00."""
        result = self.stdlib.serialize(False)
        assert result == bytes([0x20, 0x00])
    
    def test_serialize_integer(self):
        """Test serializing integer."""
        result = self.stdlib.serialize(42)
        assert result[0] == 0x21  # Integer type
    
    def test_serialize_bytes(self):
        """Test serializing bytes."""
        result = self.stdlib.serialize(b"hello")
        assert result[0] == 0x28  # ByteString type
    
    def test_serialize_list(self):
        """Test serializing list."""
        result = self.stdlib.serialize([1, 2, 3])
        assert result[0] == 0x40  # Array type
    
    def test_json_serialize(self):
        """Test JSON serialization."""
        result = self.stdlib.json_serialize({"key": "value"})
        assert b"key" in result
        assert b"value" in result
    
    def test_json_deserialize(self):
        """Test JSON deserialization."""
        result = self.stdlib.json_deserialize(b'{"key": "value"}')
        assert result == {"key": "value"}
