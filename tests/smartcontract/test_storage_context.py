"""Tests for storage context."""

from neo.smartcontract.storage_context import StorageContext
from neo.types import UInt160


class TestStorageContext:
    """Test storage context."""
    
    def test_create_context(self):
        """Test creating a storage context."""
        hash_val = UInt160(b'\x01' * 20)
        ctx = StorageContext(id=-1, script_hash=hash_val)
        assert ctx.id == -1
        assert ctx.script_hash == hash_val
        assert ctx.is_read_only is False
    
    def test_read_only_context(self):
        """Test read-only storage context."""
        hash_val = UInt160(b'\x01' * 20)
        ctx = StorageContext(id=-1, script_hash=hash_val, is_read_only=True)
        assert ctx.is_read_only is True
        assert ctx.id == -1

    def test_as_read_only(self):
        """Test converting to read-only."""
        hash_val = UInt160(b'\x01' * 20)
        ctx = StorageContext(id=-2, script_hash=hash_val)
        ro_ctx = ctx.as_read_only()
        assert ro_ctx.is_read_only is True
        assert ro_ctx.script_hash == hash_val
        assert ro_ctx.id == -2
