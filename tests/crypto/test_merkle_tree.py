"""Tests for Merkle Tree."""

import pytest
from neo.crypto.merkle import compute_root
from neo.crypto.hash import hash256


class TestMerkleTree:
    """Tests for Merkle tree operations."""
    
    def test_empty_list(self):
        """Test Merkle root of empty list."""
        result = compute_root([])
        assert result == b'\x00' * 32
    
    def test_single_hash(self):
        """Test Merkle root of single hash."""
        h = hash256(b"test")
        result = compute_root([h])
        assert result == h
    
    def test_two_hashes(self):
        """Test Merkle root of two hashes."""
        h1 = hash256(b"a")
        h2 = hash256(b"b")
        result = compute_root([h1, h2])
        expected = hash256(h1 + h2)
        assert result == expected
