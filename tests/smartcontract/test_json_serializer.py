"""Tests for JSON serializer."""

import pytest
from neo.smartcontract.json_serializer import JsonSerializer
from neo.vm.types import Integer, Boolean, ByteString, Array, NULL


class TestJsonSerializer:
    """Test JSON serialization."""
    
    def test_serialize_null(self):
        """Test null serialization."""
        data = JsonSerializer.serialize(NULL)
        assert data == b"null"
    
    def test_serialize_boolean(self):
        """Test boolean serialization."""
        assert JsonSerializer.serialize(Boolean(True)) == b"true"
        assert JsonSerializer.serialize(Boolean(False)) == b"false"
    
    def test_serialize_integer(self):
        """Test integer serialization."""
        data = JsonSerializer.serialize(Integer(42))
        assert data == b"42"
    
    def test_roundtrip_array(self):
        """Test array roundtrip."""
        arr = Array(items=[Integer(1), Integer(2)])
        data = JsonSerializer.serialize(arr)
        result = JsonSerializer.deserialize(data)
        assert len(result._items) == 2
