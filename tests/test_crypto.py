"""Tests for crypto functions."""

from neo.crypto import sha256, hash160, hash256


def test_sha256():
    """Test SHA-256."""
    result = sha256(b"hello")
    assert len(result) == 32


def test_hash256():
    """Test double SHA-256."""
    result = hash256(b"hello")
    assert len(result) == 32


def test_hash160():
    """Test Hash160."""
    result = hash160(b"hello")
    assert len(result) == 20
