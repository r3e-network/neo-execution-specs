"""Tests for Pointer type."""

import pytest
from neo.vm.types.pointer import Pointer
from neo.vm.types.stack_item import StackItemType


class TestPointer:
    """Tests for Pointer class."""
    
    def test_create_pointer(self):
        """Test creating a pointer."""
        script = bytes([0x10, 0x11, 0x12])
        ptr = Pointer(script, 1)
        assert ptr.script == script
        assert ptr.position == 1
    
    def test_pointer_type(self):
        """Test pointer type."""
        ptr = Pointer(b"", 0)
        assert ptr.type == StackItemType.POINTER
    
    def test_pointer_equality_same_script(self):
        """Test pointer equality with same script object."""
        script = bytes([0x10, 0x11])
        ptr1 = Pointer(script, 0)
        ptr2 = Pointer(script, 0)
        ptr3 = Pointer(script, 1)
        # Same script object and position
        assert ptr1 == ptr2
        # Different position
        assert ptr1 != ptr3
    
    def test_pointer_different_positions(self):
        """Test pointers with different positions."""
        script = bytes([0x10, 0x11, 0x12])
        ptr1 = Pointer(script, 0)
        ptr2 = Pointer(script, 1)
        assert ptr1 != ptr2
    
    def test_pointer_get_boolean(self):
        """Test pointer boolean conversion."""
        ptr = Pointer(b"", 0)
        assert ptr.get_boolean() is True
    
    def test_pointer_negative_position_raises(self):
        """Test that negative position raises ValueError."""
        with pytest.raises(ValueError):
            Pointer(b"", -1)
    
    def test_pointer_hash(self):
        """Test pointer hash."""
        script = bytes([0x10])
        ptr1 = Pointer(script, 0)
        ptr2 = Pointer(script, 0)
        # Same script and position should have same hash
        assert hash(ptr1) == hash(ptr2)
    
    def test_pointer_repr(self):
        """Test pointer string representation."""
        ptr = Pointer(b"", 5)
        assert "5" in repr(ptr)
