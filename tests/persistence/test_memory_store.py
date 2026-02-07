"""Tests for persistence layer."""

import pytest
from neo.persistence.memory_store import MemoryStore
from neo.persistence.snapshot import Snapshot
from neo.persistence.data_cache import DataCache
from neo.persistence.seek_direction import SeekDirection


class TestMemoryStore:
    """Tests for MemoryStore."""
    
    def test_put_get(self):
        """Test basic put and get."""
        store = MemoryStore()
        store.put(b'key1', b'value1')
        assert store.get(b'key1') == b'value1'
    
    def test_get_nonexistent(self):
        """Test getting nonexistent key."""
        store = MemoryStore()
        assert store.get(b'missing') is None
    
    def test_delete(self):
        """Test delete operation."""
        store = MemoryStore()
        store.put(b'key1', b'value1')
        store.delete(b'key1')
        assert store.get(b'key1') is None
    
    def test_contains(self):
        """Test contains check."""
        store = MemoryStore()
        store.put(b'key1', b'value1')
        assert store.contains(b'key1')
        assert not store.contains(b'missing')
    
    def test_seek_forward(self):
        """Test forward seek."""
        store = MemoryStore()
        store.put(b'a', b'1')
        store.put(b'b', b'2')
        store.put(b'c', b'3')
        
        results = list(store.seek(b'', SeekDirection.FORWARD))
        assert len(results) == 3
        assert results[0][0] == b'a'
    
    def test_seek_backward(self):
        """Test backward seek with matching prefix."""
        store = MemoryStore()
        store.put(b'a', b'1')
        store.put(b'b', b'2')
        store.put(b'c', b'3')
        
        # Seek with empty prefix to get all items
        results = list(store.seek(b'', -1))  # Use -1 for backward
        assert len(results) == 3
    
    def test_seek_with_prefix(self):
        """Test seek with prefix."""
        store = MemoryStore()
        store.put(b'prefix_a', b'1')
        store.put(b'prefix_b', b'2')
        store.put(b'other', b'3')
        
        results = list(store.seek(b'prefix_', SeekDirection.FORWARD))
        assert len(results) >= 2


class TestSeekDirection:
    """Tests for SeekDirection enum."""
    
    def test_forward(self):
        """Test forward direction."""
        assert SeekDirection.FORWARD == 1

    def test_backward(self):
        """Test backward direction."""
        assert SeekDirection.BACKWARD == -1
