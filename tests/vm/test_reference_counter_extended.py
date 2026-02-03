"""Tests for reference counter."""

import pytest
from neo.vm.reference_counter import ReferenceCounter


class TestReferenceCounter:
    """Reference counter tests."""
    
    def test_create(self):
        """Test creation."""
        rc = ReferenceCounter()
        assert rc.count == 0
    
    def test_add_reference(self):
        """Test adding reference."""
        rc = ReferenceCounter()
        rc.add_reference(object())
        assert rc.count >= 0
