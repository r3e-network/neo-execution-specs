"""Tests for VM types."""

import pytest
from neo.vm.types import Integer, ByteString, Array, Map, Boolean, Struct


class TestVMTypes:
    """VM type tests."""
    
    def test_integer_creation(self):
        """Test integer creation."""
        i = Integer(42)
        assert i.get_integer() == 42
    
    def test_integer_negative(self):
        """Test negative integer."""
        i = Integer(-100)
        assert i.get_integer() == -100
    
    def test_bytestring_creation(self):
        """Test bytestring creation."""
        bs = ByteString(b"hello")
        assert bs.value == b"hello"
    
    def test_array_creation(self):
        """Test array creation."""
        arr = Array(items=[Integer(1), Integer(2)])
        assert len(arr) == 2
    
    def test_map_creation(self):
        """Test map creation."""
        m = Map()
        assert len(m) == 0
    
    def test_boolean_true(self):
        """Test boolean true."""
        b = Boolean(True)
        assert b.get_boolean() is True
    
    def test_boolean_false(self):
        """Test boolean false."""
        b = Boolean(False)
        assert b.get_boolean() is False
