"""Tests for memory store."""

import pytest
from neo.persistence.memory_store import MemoryStore


class TestMemoryStore:
    """Test memory store."""
    
    def test_put_and_get(self):
        """Test put and get operations."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        assert store.get(b"key1") == b"value1"
    
    def test_contains(self):
        """Test contains operation."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        assert store.contains(b"key1") is True
        assert store.contains(b"key2") is False
    
    def test_delete(self):
        """Test delete operation."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        store.delete(b"key1")
        assert store.get(b"key1") is None
    
    def test_seek(self):
        """Test seek operation."""
        store = MemoryStore()
        store.put(b"prefix_a", b"val_a")
        store.put(b"prefix_b", b"val_b")
        results = list(store.seek(b"prefix_"))
        assert len(results) == 2
