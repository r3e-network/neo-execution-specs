"""Tests for MemoryPool."""

import pytest
from neo.ledger.mempool import MemoryPool
from neo.ledger.verify_result import VerifyResult
from neo.network.payloads.transaction import Transaction


class TestMemoryPool:
    """Test cases for MemoryPool."""
    
    def test_empty_pool(self):
        """Test empty pool behavior."""
        pool = MemoryPool()
        assert pool.count == 0
        assert pool.verified_count == 0
        assert pool.unverified_count == 0
    
    def test_add_transaction(self):
        """Test adding a transaction."""
        pool = MemoryPool()
        tx = Transaction(nonce=1)
        
        result = pool.try_add(tx)
        assert result == VerifyResult.SUCCEED
        assert pool.count == 1
    
    def test_duplicate_transaction(self):
        """Test adding duplicate transaction."""
        pool = MemoryPool()
        tx = Transaction(nonce=1)
        
        pool.try_add(tx)
        result = pool.try_add(tx)
        assert result == VerifyResult.ALREADY_IN_POOL
    
    def test_contains_key(self):
        """Test contains_key method."""
        pool = MemoryPool()
        tx = Transaction(nonce=1)
        
        assert not pool.contains_key(tx.hash)
        pool.try_add(tx)
        assert pool.contains_key(tx.hash)
    
    def test_remove_transaction(self):
        """Test removing a transaction."""
        pool = MemoryPool()
        tx = Transaction(nonce=1)
        
        pool.try_add(tx)
        assert pool.remove(tx.hash) is True
        assert pool.count == 0
    
    def test_clear(self):
        """Test clearing the pool."""
        pool = MemoryPool()
        tx = Transaction(nonce=1)
        
        pool.try_add(tx)
        pool.clear()
        assert pool.count == 0
        assert pool.verified_count == 0
