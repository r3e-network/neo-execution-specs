"""Tests for Murmur3 hash implementation."""

import pytest
from neo.crypto.murmur3 import murmur32


class TestMurmur32:
    """Tests for murmur32 hash function."""
    
    def test_empty_input(self):
        """Test hash of empty bytes."""
        h = murmur32(b"")
        assert isinstance(h, int)
        assert 0 <= h < 2**32
    
    def test_basic_hash(self):
        """Test basic hash computation."""
        h = murmur32(b"hello")
        assert isinstance(h, int)
        assert 0 <= h < 2**32
    
    def test_deterministic(self):
        """Test that same input produces same output."""
        h1 = murmur32(b"test")
        h2 = murmur32(b"test")
        assert h1 == h2
    
    def test_different_inputs(self):
        """Test that different inputs produce different outputs."""
        h1 = murmur32(b"hello")
        h2 = murmur32(b"world")
        assert h1 != h2
    
    def test_seed_affects_output(self):
        """Test that different seeds produce different outputs."""
        h1 = murmur32(b"test", seed=0)
        h2 = murmur32(b"test", seed=1)
        assert h1 != h2
    
    def test_known_values(self):
        """Test against known Murmur3 values."""
        # These are standard test vectors
        assert murmur32(b"", 0) == 0
        assert murmur32(b"", 1) == 0x514e28b7
        assert murmur32(b"", 0xffffffff) == 0x81f16f39
    
    def test_various_lengths(self):
        """Test with various input lengths."""
        for length in [1, 2, 3, 4, 5, 7, 8, 15, 16, 31, 32, 100]:
            data = bytes(range(length % 256)) * (length // 256 + 1)
            data = data[:length]
            h = murmur32(data)
            assert isinstance(h, int)
            assert 0 <= h < 2**32
    
    def test_alignment(self):
        """Test with inputs of different alignments."""
        # 1 byte
        h1 = murmur32(b"a")
        # 2 bytes
        h2 = murmur32(b"ab")
        # 3 bytes
        h3 = murmur32(b"abc")
        # 4 bytes (aligned)
        h4 = murmur32(b"abcd")
        
        # All should be different
        assert len({h1, h2, h3, h4}) == 4
    
    def test_large_input(self):
        """Test with large input."""
        data = b"x" * 10000
        h = murmur32(data)
        assert isinstance(h, int)
        assert 0 <= h < 2**32
