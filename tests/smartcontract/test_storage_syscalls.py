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
        """Build storage key from script hash and key."""
        script_hash = UInt160(b"\x01" * 20)
        key = b"test_key"
        
        result = storage._build_storage_key(script_hash, key)
        
        assert result == bytes(script_hash) + key
        assert len(result) == 28


class TestStorageContext:
    """Storage context tests."""
    
    def test_create_context(self):
        """Test storage context creation."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(script_hash, is_read_only=False)
        
        assert ctx.script_hash == script_hash
        assert ctx.is_read_only is False
    
    def test_read_only_context(self):
        """Test read-only storage context."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(script_hash, is_read_only=True)
        
        assert ctx.is_read_only is True
