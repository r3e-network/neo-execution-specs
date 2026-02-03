"""Tests for Bloom filter implementation."""

import pytest
from neo.crypto.bloom_filter import BloomFilter


class TestBloomFilter:
    """Tests for BloomFilter class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        bf = BloomFilter(m=64, k=3)
        assert bf.m == 64
        assert bf.k == 3
        assert len(bf.bits) == 8  # 64 bits = 8 bytes
    
    def test_init_rounds_up(self):
        """Test that m is rounded up to multiple of 8."""
        bf = BloomFilter(m=65, k=3)
        assert bf.m == 72  # Rounded up to 72
        assert len(bf.bits) == 9
    
    def test_init_invalid_m(self):
        """Test that invalid m raises error."""
        with pytest.raises(ValueError):
            BloomFilter(m=0, k=3)
        with pytest.raises(ValueError):
            BloomFilter(m=-1, k=3)
    
    def test_init_invalid_k(self):
        """Test that invalid k raises error."""
        with pytest.raises(ValueError):
            BloomFilter(m=64, k=0)
        with pytest.raises(ValueError):
            BloomFilter(m=64, k=-1)
    
    def test_add_and_check(self):
        """Test adding and checking elements."""
        bf = BloomFilter(m=1024, k=5)
        
        # Add some elements
        bf.add(b"hello")
        bf.add(b"world")
        bf.add(b"neo")
        
        # Check they're present
        assert bf.check(b"hello")
        assert bf.check(b"world")
        assert bf.check(b"neo")
    
    def test_check_not_present(self):
        """Test checking elements not in filter."""
        bf = BloomFilter(m=1024, k=5)
        bf.add(b"hello")
        
        # Elements not added should (usually) not be found
        # Note: false positives are possible but unlikely with good params
        assert not bf.check(b"goodbye")
        assert not bf.check(b"test123")
    
    def test_contains_operator(self):
        """Test 'in' operator support."""
        bf = BloomFilter(m=1024, k=5)
        bf.add(b"test")
        
        assert b"test" in bf
        assert b"other" not in bf
    
    def test_clear(self):
        """Test clearing the filter."""
        bf = BloomFilter(m=64, k=3)
        bf.add(b"hello")
        assert bf.check(b"hello")
        
        bf.clear()
        assert not bf.check(b"hello")
        assert bf.bits == bytearray(8)
    
    def test_get_and_load_bits(self):
        """Test getting and loading raw bits."""
        bf1 = BloomFilter(m=64, k=3)
        bf1.add(b"hello")
        bf1.add(b"world")
        
        bits = bf1.get_bits()
        
        bf2 = BloomFilter(m=64, k=3)
        bf2.load_bits(bits)
        
        assert bf2.check(b"hello")
        assert bf2.check(b"world")
    
    def test_load_bits_wrong_size(self):
        """Test loading bits with wrong size raises error."""
        bf = BloomFilter(m=64, k=3)
        with pytest.raises(ValueError):
            bf.load_bits(b"wrong")
    
    def test_optimal_k(self):
        """Test optimal k calculation."""
        # For m=1000, n=100, optimal k ≈ 7
        k = BloomFilter.optimal_k(1000, 100)
        assert 5 <= k <= 10
        
        # Edge case: n=0
        assert BloomFilter.optimal_k(1000, 0) == 1
    
    def test_optimal_m(self):
        """Test optimal m calculation."""
        # For n=100 elements, p=0.01 (1% false positive)
        m = BloomFilter.optimal_m(100, 0.01)
        assert m > 0
        
        # Lower false positive rate needs more bits
        m_low = BloomFilter.optimal_m(100, 0.001)
        assert m_low > m
    
    def test_optimal_m_invalid(self):
        """Test optimal_m with invalid parameters."""
        with pytest.raises(ValueError):
            BloomFilter.optimal_m(0, 0.01)
        with pytest.raises(ValueError):
            BloomFilter.optimal_m(100, 0)
        with pytest.raises(ValueError):
            BloomFilter.optimal_m(100, 1)
    
    def test_properties(self):
        """Test size and hash_count properties."""
        bf = BloomFilter(m=128, k=7)
        assert bf.size == 128
        assert bf.hash_count == 7
    
    def test_different_seeds(self):
        """Test that different seeds produce different results."""
        bf1 = BloomFilter(m=64, k=3, seed=0)
        bf2 = BloomFilter(m=64, k=3, seed=12345)
        
        bf1.add(b"test")
        bf2.add(b"test")
        
        # Different seeds should set different bits
        assert bf1.get_bits() != bf2.get_bits()
    
    def test_many_elements(self):
        """Test with many elements."""
        bf = BloomFilter(m=10000, k=7)
        
        # Add 100 elements
        for i in range(100):
            bf.add(f"element_{i}".encode())
        
        # All should be found
        for i in range(100):
            assert bf.check(f"element_{i}".encode())
    
    def test_empty_element(self):
        """Test with empty bytes."""
        bf = BloomFilter(m=64, k=3)
        bf.add(b"")
        assert bf.check(b"")
