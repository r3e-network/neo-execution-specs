"""Tests for reference counter."""

import pytest
from neo.vm.reference_counter import ReferenceCounter


class TestReferenceCounter:
    """Tests for ReferenceCounter."""
    
    def test_create(self):
        """Test creating reference counter."""
        rc = ReferenceCounter()
        assert rc is not None
    
    def test_count(self):
        """Test count property."""
        rc = ReferenceCounter()
        assert rc.count >= 0
