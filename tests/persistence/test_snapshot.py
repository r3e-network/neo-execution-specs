"""Tests for Snapshot."""

import pytest
from neo.persistence.snapshot import MemorySnapshot, StoreSnapshot
from neo.persistence.memory_store import MemoryStore


class TestMemorySnapshot:
    """Test MemorySnapshot functionality."""
    
    def test_get_empty(self):
        """Test get from empty snapshot."""
        snap = MemorySnapshot()
        assert snap.get(b"key") is None
    
    def test_put_and_get(self):
        """Test put and get."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        assert snap.get(b"key") == b"value"
    
    def test_contains(self):
        """Test contains."""
        snap = MemorySnapshot()
        assert not snap.contains(b"key")
        snap.put(b"key", b"value")
        assert snap.contains(b"key")
    
    def test_delete(self):
        """Test delete."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        snap.delete(b"key")
        assert not snap.contains(b"key")
        assert snap.get(b"key") is None
    
    def test_commit(self):
        """Test commit changes."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        snap.commit()
        # After commit, value should be in store
        assert snap.get(b"key") == b"value"
    
    def test_find(self):
        """Test find with prefix."""
        snap = MemorySnapshot()
        snap.put(b"prefix_1", b"v1")
        snap.put(b"prefix_2", b"v2")
        snap.put(b"other", b"v3")
        snap.commit()
        
        results = list(snap.find(b"prefix_"))
        assert len(results) == 2
    
    def test_clone(self):
        """Test clone snapshot."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        
        clone = snap.clone()
        assert clone.get(b"key") == b"value"
        
        # Changes to clone don't affect original
        clone.put(b"key2", b"value2")
        assert snap.get(b"key2") is None
    
    def test_get_and_change(self):
        """Test get_and_change."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        snap.commit()
        
        value = snap.get_and_change(b"key")
        assert value == b"value"
        
        # With factory
        value = snap.get_and_change(b"new", lambda: b"created")
        assert value == b"created"
    
    def test_add_existing_raises(self):
        """Test add raises for existing key."""
        snap = MemorySnapshot()
        snap.put(b"key", b"value")
        snap.commit()
        
        with pytest.raises(KeyError):
            snap.add(b"key", b"other")


class TestStoreSnapshot:
    """Test StoreSnapshot functionality."""
    
    def test_get_from_store(self):
        """Test get from underlying store."""
        store = MemoryStore()
        store.put(b"key", b"value")
        snap = StoreSnapshot(store)
        assert snap.get(b"key") == b"value"
    
    def test_put_and_get(self):
        """Test put and get."""
        store = MemoryStore()
        snap = StoreSnapshot(store)
        snap.put(b"key", b"value")
        assert snap.get(b"key") == b"value"
        # Not yet in store
        assert store.get(b"key") is None
    
    def test_commit(self):
        """Test commit to store."""
        store = MemoryStore()
        snap = StoreSnapshot(store)
        snap.put(b"key", b"value")
        snap.commit()
        assert store.get(b"key") == b"value"
    
    def test_delete_and_commit(self):
        """Test delete and commit."""
        store = MemoryStore()
        store.put(b"key", b"value")
        snap = StoreSnapshot(store)
        snap.delete(b"key")
        snap.commit()
        assert store.get(b"key") is None
    
    def test_find(self):
        """Test find with prefix."""
        store = MemoryStore()
        store.put(b"prefix_1", b"v1")
        store.put(b"prefix_2", b"v2")
        snap = StoreSnapshot(store)
        snap.put(b"prefix_3", b"v3")
        
        results = list(snap.find(b"prefix_"))
        assert len(results) == 3
