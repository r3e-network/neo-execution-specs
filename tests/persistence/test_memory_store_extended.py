"""Tests for persistence module."""

import pytest
from neo.persistence.memory_store import MemoryStore
from neo.persistence.data_cache import DataCache


class TestMemoryStoreExtended:
    """Extended memory store tests."""
    
    def test_put_get(self):
        """Test put and get."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        assert store.get(b"key1") == b"value1"
    
    def test_delete(self):
        """Test delete."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        store.delete(b"key1")
        assert store.get(b"key1") is None
    
    def test_contains(self):
        """Test contains."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        assert store.contains(b"key1")
        assert not store.contains(b"key2")
