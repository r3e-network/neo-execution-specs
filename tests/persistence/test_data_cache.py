"""Tests for DataCache."""

from neo.persistence.memory_store import MemoryStore
from neo.persistence.data_cache import DataCache, ClonedCache


class TestDataCache:
    """Test DataCache functionality."""
    
    def test_get_from_empty(self):
        """Test get from empty cache."""
        store = MemoryStore()
        cache = DataCache(store)
        assert cache.get(b"key") is None
    
    def test_put_and_get(self):
        """Test put and get."""
        store = MemoryStore()
        cache = DataCache(store)
        cache.put(b"key", b"value")
        assert cache.get(b"key") == b"value"
    
    def test_contains(self):
        """Test contains."""
        store = MemoryStore()
        cache = DataCache(store)
        assert not cache.contains(b"key")
        cache.put(b"key", b"value")
        assert cache.contains(b"key")
    
    def test_delete(self):
        """Test delete."""
        store = MemoryStore()
        cache = DataCache(store)
        cache.put(b"key", b"value")
        assert cache.contains(b"key")
        cache.delete(b"key")
        assert not cache.contains(b"key")
    
    def test_get_from_store(self):
        """Test get from underlying store."""
        store = MemoryStore()
        store.put(b"key", b"value")
        cache = DataCache(store)
        assert cache.get(b"key") == b"value"
    
    def test_delete_from_store(self):
        """Test delete key from store."""
        store = MemoryStore()
        store.put(b"key", b"value")
        cache = DataCache(store)
        cache.delete(b"key")
        assert cache.get(b"key") is None
    
    def test_commit(self):
        """Test commit changes to store."""
        store = MemoryStore()
        cache = DataCache(store)
        cache.put(b"key1", b"value1")
        cache.put(b"key2", b"value2")
        cache.commit()
        assert store.get(b"key1") == b"value1"
        assert store.get(b"key2") == b"value2"
    
    def test_commit_delete(self):
        """Test commit with deletes."""
        store = MemoryStore()
        store.put(b"key", b"value")
        cache = DataCache(store)
        cache.delete(b"key")
        cache.commit()
        assert store.get(b"key") is None
    
    def test_try_get(self):
        """Test try_get."""
        store = MemoryStore()
        cache = DataCache(store)
        found, value = cache.try_get(b"key")
        assert not found
        assert value is None
        
        cache.put(b"key", b"value")
        found, value = cache.try_get(b"key")
        assert found
        assert value == b"value"
    
    def test_get_or_add(self):
        """Test get_or_add."""
        store = MemoryStore()
        cache = DataCache(store)
        value = cache.get_or_add(b"key", lambda: b"new_value")
        assert value == b"new_value"
        
        # Should return existing value
        value = cache.get_or_add(b"key", lambda: b"other")
        assert value == b"new_value"
    
    def test_get_and_change(self):
        """Test get_and_change."""
        store = MemoryStore()
        store.put(b"key", b"value")
        cache = DataCache(store)
        
        value = cache.get_and_change(b"key")
        assert value == b"value"
        
        # With factory for non-existent key
        value = cache.get_and_change(b"new", lambda: b"created")
        assert value == b"created"
    
    def test_find(self):
        """Test find with prefix."""
        store = MemoryStore()
        store.put(b"prefix_1", b"v1")
        store.put(b"prefix_2", b"v2")
        store.put(b"other", b"v3")
        cache = DataCache(store)
        cache.put(b"prefix_3", b"v4")
        
        results = list(cache.find(b"prefix_"))
        assert len(results) == 3
        keys = [k for k, v in results]
        assert b"prefix_1" in keys
        assert b"prefix_2" in keys
        assert b"prefix_3" in keys
    
    def test_change_set(self):
        """Test get_change_set."""
        store = MemoryStore()
        cache = DataCache(store)
        cache.put(b"key1", b"value1")
        cache.put(b"key2", b"value2")
        
        changes = list(cache.get_change_set())
        assert len(changes) == 2


class TestClonedCache:
    """Test ClonedCache functionality."""
    
    def test_clone_get(self):
        """Test get from cloned cache."""
        store = MemoryStore()
        parent = DataCache(store)
        parent.put(b"key", b"value")
        
        clone = ClonedCache(parent)
        assert clone.get(b"key") == b"value"
    
    def test_clone_put(self):
        """Test put in cloned cache."""
        store = MemoryStore()
        parent = DataCache(store)
        
        clone = ClonedCache(parent)
        clone.put(b"key", b"value")
        
        # Should be in clone but not parent
        assert clone.get(b"key") == b"value"
        assert parent.get(b"key") is None
    
    def test_clone_commit(self):
        """Test commit cloned cache to parent."""
        store = MemoryStore()
        parent = DataCache(store)
        
        clone = ClonedCache(parent)
        clone.put(b"key", b"value")
        clone.commit()
        
        # Now should be in parent
        assert parent.get(b"key") == b"value"
