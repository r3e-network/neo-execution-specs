"""Tests for storage module."""

import pytest
from neo.smartcontract.storage.storage_key import StorageKey


class TestStorageKey:
    """StorageKey tests."""
    
    def test_create(self):
        """Test key creation."""
        key = StorageKey(id=1, key=b"test")
        assert key.id == 1
    
    def test_to_bytes(self):
        """Test serialization."""
        key = StorageKey(id=1, key=b"test")
        data = key.to_bytes()
        assert len(data) == 8
