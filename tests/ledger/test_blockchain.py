"""Tests for Blockchain."""

import pytest
from neo.ledger.blockchain import Blockchain, ApplicationExecuted
from neo.types import UInt256
from neo.persistence.memory_store import MemoryStore


class TestApplicationExecuted:
    """Test ApplicationExecuted dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        result = ApplicationExecuted()
        assert result.tx_hash is None
        assert result.trigger == "Application"
        assert result.vm_state == "HALT"
        assert result.gas_consumed == 0
        assert result.exception is None
        assert result.stack == []
        assert result.notifications == []
    
    def test_custom_values(self):
        """Test custom values."""
        tx_hash = UInt256(bytes(32))
        result = ApplicationExecuted(
            tx_hash=tx_hash,
            trigger="Verification",
            vm_state="FAULT",
            gas_consumed=1000,
            exception="Test error"
        )
        assert result.tx_hash == tx_hash
        assert result.trigger == "Verification"
        assert result.vm_state == "FAULT"
        assert result.gas_consumed == 1000
        assert result.exception == "Test error"


class TestBlockchain:
    """Test Blockchain class."""
    
    def test_create_blockchain(self):
        """Test creating a blockchain."""
        store = MemoryStore()
        blockchain = Blockchain(store)
        assert blockchain.height == -1
        assert blockchain.current_block is None
        assert blockchain.genesis_block is None
    
    def test_height_property(self):
        """Test height property."""
        store = MemoryStore()
        blockchain = Blockchain(store)
        assert blockchain.height == -1
    
    def test_contains_block_empty(self):
        """Test contains_block on empty blockchain."""
        store = MemoryStore()
        blockchain = Blockchain(store)
        block_hash = UInt256(bytes(32))
        assert not blockchain.contains_block(block_hash)
    
    def test_get_block_not_found(self):
        """Test get_block when block doesn't exist."""
        store = MemoryStore()
        blockchain = Blockchain(store)
        block_hash = UInt256(bytes(32))
        assert blockchain.get_block(block_hash) is None
    
    def test_get_block_by_index_not_found(self):
        """Test get_block_by_index when block doesn't exist."""
        store = MemoryStore()
        blockchain = Blockchain(store)
        assert blockchain.get_block_by_index(0) is None
    
    def test_on_persist_callback(self):
        """Test on_persist callback registration."""
        store = MemoryStore()
        blockchain = Blockchain(store)
        
        callback_called = []
        def callback(block):
            callback_called.append(block)
        
        blockchain.on_persist(callback)
        # Callback should be registered
        assert len(blockchain._on_persist) == 1
    
    def test_on_committed_callback(self):
        """Test on_committed callback registration."""
        store = MemoryStore()
        blockchain = Blockchain(store)
        
        callback_called = []
        def callback(block):
            callback_called.append(block)
        
        blockchain.on_committed(callback)
        # Callback should be registered
        assert len(blockchain._on_committed) == 1
