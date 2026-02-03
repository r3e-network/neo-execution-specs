"""Tests for MemoryStore."""

import pytest
from neo.persistence.memory_store import MemoryStore


class TestMemoryStoreExtended:
    """Extended MemoryStore tests."""
    
    def test_seek_forward(self):
        """Test seek forward."""
        s = MemoryStore()
        s.put(b"a", b"1")
        s.put(b"b", b"2")
        results = list(s.seek(b"", 1))
        assert len(results) == 2
