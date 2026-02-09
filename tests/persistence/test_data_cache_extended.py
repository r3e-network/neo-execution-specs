"""Extended tests for DataCache."""

from neo.persistence.data_cache import DataCache, TrackState, Trackable
from neo.persistence.memory_store import MemoryStore


class TestDataCacheExtended:
    """Extended tests for DataCache class."""
    
    def test_create_with_store(self):
        """Test creating cache with store."""
        store = MemoryStore()
        cache = DataCache(store)
        assert cache is not None
    
    def test_get_from_store(self):
        """Test getting value from underlying store."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        cache = DataCache(store)
        assert cache.get(b"key1") == b"value1"
    
    def test_contains_in_store(self):
        """Test contains with value in store."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        cache = DataCache(store)
        assert cache.contains(b"key1") is True
        assert cache.contains(b"key2") is False
    
    def test_try_get_found(self):
        """Test try_get with existing key."""
        store = MemoryStore()
        store.put(b"key1", b"value1")
        cache = DataCache(store)
        found, value = cache.try_get(b"key1")
        assert found is True
        assert value == b"value1"
    
    def test_try_get_not_found(self):
        """Test try_get with missing key."""
        store = MemoryStore()
        cache = DataCache(store)
        found, value = cache.try_get(b"key1")
        assert found is False
        assert value is None


class TestTrackState:
    """Tests for TrackState enum."""
    
    def test_none_state(self):
        """Test NONE state."""
        assert TrackState.NONE.value == 0
    
    def test_added_state(self):
        """Test ADDED state."""
        assert TrackState.ADDED.value == 1
    
    def test_changed_state(self):
        """Test CHANGED state."""
        assert TrackState.CHANGED.value == 2
    
    def test_deleted_state(self):
        """Test DELETED state."""
        assert TrackState.DELETED.value == 3


class TestTrackable:
    """Tests for Trackable class."""
    
    def test_create_trackable(self):
        """Test creating trackable entry."""
        t = Trackable(b"key", b"value", TrackState.ADDED)
        assert t.key == b"key"
        assert t.value == b"value"
        assert t.state == TrackState.ADDED
