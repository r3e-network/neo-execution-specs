"""Tests for data cache."""

import pytest
from neo.persistence.data_cache import DataCache
from neo.persistence.memory_store import MemoryStore


class TestDataCache:
    """Data cache tests."""
    
    def test_create(self):
        """Test cache creation."""
        store = MemoryStore()
        cache = DataCache(store)
        assert cache is not None
