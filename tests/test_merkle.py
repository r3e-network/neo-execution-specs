"""Tests for Merkle tree."""

import pytest
from neo.crypto.merkle import compute_root
from neo.crypto.hash import hash256


def test_merkle_empty():
    """Test with empty list."""
    result = compute_root([])
    assert result == b'\x00' * 32


def test_merkle_single():
    """Test with single hash."""
    h = hash256(b"test")
    result = compute_root([h])
    assert result == h


def test_merkle_two():
    """Test with two hashes."""
    h1 = hash256(b"a")
    h2 = hash256(b"b")
    result = compute_root([h1, h2])
    expected = hash256(h1 + h2)
    assert result == expected
