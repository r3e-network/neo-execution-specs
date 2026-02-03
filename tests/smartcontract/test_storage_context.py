"""Tests for storage context."""

import pytest
from neo.smartcontract.storage_context import StorageContext
from neo.types import UInt160


class TestStorageContext:
    """Test storage context."""
    
    def test_create_context(self):
        """Test creating a storage context."""
        hash_val = UInt160(b'\x01' * 20)
        ctx = StorageContext(hash_val)
        assert ctx.script_hash == hash_val
        assert ctx.is_read_only is False
    
    def test_read_only_context(self):
        """Test read-only storage context."""
        hash_val = UInt160(b'\x01' * 20)
        ctx = StorageContext(hash_val, is_read_only=True)
        assert ctx.is_read_only is True
