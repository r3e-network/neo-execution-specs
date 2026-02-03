"""Tests for InteropInterface type."""

import pytest
from neo.vm.types.interop_interface import InteropInterface
from neo.vm.types.stack_item import StackItemType


class TestInteropInterface:
    """Tests for InteropInterface class."""
    
    def test_create_interop(self):
        """Test creating an interop interface."""
        obj = {"key": "value"}
        interop = InteropInterface(obj)
        assert interop.get_interface() == obj
    
    def test_interop_type(self):
        """Test interop interface type."""
        interop = InteropInterface(None)
        assert interop.type == StackItemType.INTEROP_INTERFACE
    
    def test_interop_get_boolean(self):
        """Test interop boolean conversion."""
        interop = InteropInterface("test")
        assert interop.get_boolean() is True
    
    def test_interop_with_none(self):
        """Test interop with None object."""
        interop = InteropInterface(None)
        assert interop.get_interface() is None
    
    def test_interop_equality(self):
        """Test interop equality."""
        obj = [1, 2, 3]
        interop1 = InteropInterface(obj)
        interop2 = InteropInterface(obj)
        interop3 = InteropInterface([1, 2, 3])
        # Same object reference
        assert interop1 == interop2
        # Different object (even with same content)
        assert interop1 != interop3
    
    def test_interop_hash(self):
        """Test interop hash."""
        obj = "test"
        interop = InteropInterface(obj)
        # Should be hashable
        h = hash(interop)
        assert isinstance(h, int)
    
    def test_interop_get_interface(self):
        """Test get_interface method."""
        obj = {"data": 123}
        interop = InteropInterface(obj)
        result = interop.get_interface()
        assert result == obj
    
    def test_interop_repr(self):
        """Test string representation."""
        interop = InteropInterface("test")
        assert "str" in repr(interop)
