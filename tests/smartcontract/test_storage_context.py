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
