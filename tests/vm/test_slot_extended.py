"""Tests for slot system."""

import pytest
from neo.vm.slot import Slot
from neo.vm.types import Integer


class TestSlot:
    """Slot tests."""
    
    def test_create_slot(self):
        """Test slot creation."""
        slot = Slot(5)
        assert len(slot) == 5
    
    def test_get_set(self):
        """Test get and set."""
        slot = Slot(3)
        slot[0] = Integer(42)
        assert slot[0].get_integer() == 42
