"""Tests for persistence module."""

import pytest
from neo.persistence import MemorySnapshot, ClonedCache


class TestSnapshot:
    """Snapshot tests."""
    
    def test_put_get(self):
        """Test put and get."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        assert snap.get(b"key") == b"value"
    
    def test_delete(self):
        """Test delete."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        snap.delete(b"key")
        assert snap.get(b"key") is None


class TestClonedCache:
    """ClonedCache tests."""
    
    def test_add_get(self):
        """Test add and get."""
        cache = ClonedCache()
        cache.add(b"key", "value")
        assert cache.get(b"key") == "value"
