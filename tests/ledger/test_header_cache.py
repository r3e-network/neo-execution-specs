"""Tests for HeaderCache."""

from neo.ledger.header_cache import HeaderCache
from neo.network.payloads.header import Header


class TestHeaderCache:
    """Test cases for HeaderCache."""
    
    def test_empty_cache(self):
        """Test empty cache behavior."""
        cache = HeaderCache()
        assert cache.count == 0
        assert cache.last is None
        assert cache[0] is None
        assert not cache.full
    
    def test_add_header(self):
        """Test adding headers."""
        cache = HeaderCache()
        header = Header(index=0)
        
        assert cache.add(header) is True
        assert cache.count == 1
        assert cache.last == header
    
    def test_get_by_index(self):
        """Test getting header by index."""
        cache = HeaderCache()
        h0 = Header(index=0)
        h1 = Header(index=1)
        
        cache.add(h0)
        cache.add(h1)
        
        assert cache[0] == h0
        assert cache[1] == h1
        assert cache[2] is None
    
    def test_remove_first(self):
        """Test removing first header."""
        cache = HeaderCache()
        h0 = Header(index=0)
        cache.add(h0)
        
        removed = cache.try_remove_first()
        assert removed == h0
        assert cache.count == 0
    
    def test_iteration(self):
        """Test iterating over headers."""
        cache = HeaderCache()
        headers = [Header(index=i) for i in range(3)]
        for h in headers:
            cache.add(h)
        
        result = list(cache)
        assert result == headers
