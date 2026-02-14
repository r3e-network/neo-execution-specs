"""Tests for crypto module."""

from neo.crypto.hash import hash160, hash256, sha256


class TestHash:
    """Hash tests."""

    def test_hash160(self):
        """Test hash160."""
        result = hash160(b"test")
        assert len(result) == 20

    def test_hash256(self):
        """Test hash256."""
        result = hash256(b"test")
        assert len(result) == 32

    def test_hash160_known_vector(self):
        """SHA256 then RIPEMD160 of 'test'."""
        result = hash160(b"test")
        assert result.hex() == "cebaa98c19807134434d107b0d3e5692a516ea66"

    def test_hash256_known_vector(self):
        """Double SHA256 of 'test'."""
        result = hash256(b"test")
        assert result.hex() == "954d5a49fd70d9b8bcdb35d252267829957f7ef7fa6c74f88419bdc5e82209f4"

    def test_sha256_known_vector(self):
        """SHA256 of 'test'."""
        result = sha256(b"test")
        assert result.hex() == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

    def test_hash_empty_input(self):
        """Edge case: empty input."""
        result = hash160(b"")
        assert len(result) == 20
        result = hash256(b"")
        assert len(result) == 32
