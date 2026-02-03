"""Extended tests for DataCache."""

import pytest
from neo.persistence.data_cache import DataCache, TrackState


class TestDataCacheExtended:
    """Extended tests for DataCache class."""
    
    def test_create_empty(self):
        """Test creating empty cache."""
        cache = DataCache()
        assert len(cache) == 0
    
    def test_add_item(self):
        """Test adding item to cache."""
        cache = DataCache()
        cache.add(b"key1", b"value1")
        assert cache.try_get(b"key1") == b"value1"
    
    def test_delete_item(self):
        """Test deleting item from cache."""
        cache = DataCache()
        cache.add(b"key1", b"value1")
        cache.delete(b"key1")
        assert cache.try_get(b"key1") is None
    
    def test_get_or_add_existing(self):
        """Test get_or_add with existing key."""
        cache = DataCache()
        cache.add(b"key1", b"value1")
        result = cache.get_or_add(b"key1", lambda: b"new_value")
        assert result == b"value1"
    
    def test_get_or_add_new(self):
        """Test get_or_add with new key."""
        cache = DataCache()
        result = cache.get_or_add(b"key1", lambda: b"new_value")
        assert result == b"new_value"
    
    def test_get_and_change(self):
        """Test get_and_change method."""
        cache = DataCache()
        cache.add(b"key1", b"value1")
        result = cache.get_and_change(b"key1")
        assert result == b"value1"


class TestTrackState:
    """Tests for TrackState enum."""
    
    def test_none_state(self):
        """Test NONE state."""
        assert TrackState.NONE == 0
    
    def test_added_state(self):
        """Test ADDED state."""
        assert TrackState.ADDED == 1
    
    def test_changed_state(self):
        """Test CHANGED state."""
        assert TrackState.CHANGED == 2
    
    def test_deleted_state(self):
        """Test DELETED state."""
        assert TrackState.DELETED == 3
