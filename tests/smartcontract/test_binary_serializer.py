"""Tests for binary serializer."""

from neo.smartcontract.binary_serializer import BinarySerializer
from neo.vm.types import Integer, Boolean, ByteString, Array, NULL


class TestBinarySerializer:
    """Test binary serialization."""
    
    def test_serialize_null(self):
        """Test null serialization."""
        data = BinarySerializer.serialize(NULL)
        assert data[0] == 0x00  # ANY type
    
    def test_serialize_boolean_true(self):
        """Test true serialization."""
        data = BinarySerializer.serialize(Boolean(True))
        assert data == bytes([0x20, 1])
    
    def test_serialize_boolean_false(self):
        """Test false serialization."""
        data = BinarySerializer.serialize(Boolean(False))
        assert data == bytes([0x20, 0])
    
    def test_serialize_integer_zero(self):
        """Test zero integer serialization."""
        data = BinarySerializer.serialize(Integer(0))
        assert data == bytes([0x21, 0])
    
    def test_serialize_integer_positive(self):
        """Test positive integer serialization."""
        data = BinarySerializer.serialize(Integer(42))
        result = BinarySerializer.deserialize(data)
        assert result.value == 42
    
    def test_serialize_bytestring(self):
        """Test bytestring serialization."""
        data = BinarySerializer.serialize(ByteString(b"hello"))
        result = BinarySerializer.deserialize(data)
        assert result.value == b"hello"
    
    def test_serialize_array(self):
        """Test array serialization."""
        arr = Array(items=[Integer(1), Integer(2)])
        data = BinarySerializer.serialize(arr)
        result = BinarySerializer.deserialize(data)
        assert len(result._items) == 2
