"""Tests for Bloom Filter."""

from neo.crypto.bloom_filter import BloomFilter


class TestBloomFilter:
    """Tests for BloomFilter."""
    
    def test_create_filter(self):
        """Test creating a bloom filter."""
        bf = BloomFilter(m=100, k=3)
        assert bf.m == 100
        assert bf.k == 3
        assert len(bf.bits) == 13  # ceil(100/8)
    
    def test_add_and_contains(self):
        """Test adding elements and checking membership."""
        bf = BloomFilter(m=1000, k=5)
        bf.add(b"hello")
        bf.add(b"world")
        
        assert bf.check(b"hello") is True
        assert bf.check(b"world") is True
    
    def test_false_negative_impossible(self):
        """Test that false negatives are impossible."""
        bf = BloomFilter(m=1000, k=5)
        items = [f"item{i}".encode() for i in range(100)]
        
        for item in items:
            bf.add(item)
        
        # All added items must be found
        for item in items:
            assert bf.check(item) is True
