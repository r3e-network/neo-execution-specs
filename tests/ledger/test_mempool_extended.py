"""Tests for mempool functionality."""

from neo.ledger.mempool import MemoryPool
from neo.ledger.verify_result import VerifyResult
from neo.network.payloads.transaction import Transaction
from neo.network.payloads.signer import Signer
from neo.types.uint160 import UInt160


class TestMemoryPool:
    """Memory pool tests."""
    
    def test_create_pool(self):
        """Test pool creation."""
        pool = MemoryPool()
        assert pool.capacity == MemoryPool.DEFAULT_CAPACITY
        assert pool.count == 0
    
    def test_custom_capacity(self):
        """Test custom capacity."""
        pool = MemoryPool(capacity=1000)
        assert pool.capacity == 1000
    
    def test_add_transaction(self):
        """Test adding transaction."""
        pool = MemoryPool()
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(script=b"\x40", signers=[signer])
        
        result = pool.try_add(tx)
        assert result == VerifyResult.SUCCEED
        assert pool.count == 1
    
    def test_add_duplicate(self):
        """Test adding duplicate transaction."""
        pool = MemoryPool()
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(script=b"\x40", signers=[signer])
        
        pool.try_add(tx)
        result = pool.try_add(tx)
        assert result == VerifyResult.ALREADY_IN_POOL
    
    def test_contains_key(self):
        """Test contains key."""
        pool = MemoryPool()
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(script=b"\x40", signers=[signer])
        
        pool.try_add(tx)
        assert pool.contains_key(tx.hash)
    
    def test_try_get(self):
        """Test try get."""
        pool = MemoryPool()
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(script=b"\x40", signers=[signer])
        
        pool.try_add(tx)
        retrieved = pool.try_get(tx.hash)
        assert retrieved is not None
    
    def test_remove(self):
        """Test remove transaction."""
        pool = MemoryPool()
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(script=b"\x40", signers=[signer])
        
        pool.try_add(tx)
        assert pool.remove(tx.hash)
        assert pool.count == 0
    
    def test_clear(self):
        """Test clear pool."""
        pool = MemoryPool()
        signer = Signer(account=UInt160(b"\x01" * 20))
        
        for i in range(5):
            tx = Transaction(
                script=bytes([0x40 + i]),
                signers=[signer],
                nonce=i
            )
            pool.try_add(tx)
        
        assert pool.count == 5
        pool.clear()
        assert pool.count == 0
