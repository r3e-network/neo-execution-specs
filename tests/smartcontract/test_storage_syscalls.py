"""Tests for storage syscalls."""

from neo.smartcontract.syscalls import storage
from neo.smartcontract.storage_context import StorageContext
from neo.types.uint160 import UInt160


class TestStorageSyscalls:
    """Storage syscall tests."""
    
    def test_storage_price_constant(self):
        """Storage price should be defined."""
        assert storage.STORAGE_PRICE == 100000
    
    def test_build_storage_key(self):
        """Build storage key from context contract ID (int32 LE) + user key."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(id=-3, script_hash=script_hash)
        key = b"test_key"

        result = storage._build_storage_key(ctx, key)

        expected_id = (-3).to_bytes(4, byteorder="little", signed=True)
        assert result == expected_id + key
        assert len(result) == 4 + len(key)


class TestStorageContext:
    """Storage context tests."""
    
    def test_create_context(self):
        """Test storage context creation."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(id=-1, script_hash=script_hash, is_read_only=False)

        assert ctx.script_hash == script_hash
        assert ctx.is_read_only is False
    
    def test_read_only_context(self):
        """Test read-only storage context."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(id=-1, script_hash=script_hash, is_read_only=True)

        assert ctx.is_read_only is True
