"""Tests for blockchain functionality."""

from neo.ledger.blockchain import Blockchain, ApplicationExecuted
from neo.network.payloads.block import Block
from neo.network.payloads.witness import Witness
from neo.persistence.memory_store import MemoryStore


class TestBlockchain:
    """Blockchain tests."""
    
    def test_create_blockchain(self):
        """Test blockchain creation."""
        store = MemoryStore()
        bc = Blockchain(store)
        assert bc.height == -1
    
    def test_persist_genesis(self):
        """Test persisting genesis block."""
        store = MemoryStore()
        bc = Blockchain(store)
        
        block = Block(
            index=0,
            witness=Witness(b"\x00", b"\x00")
        )
        
        bc.persist(block)
        assert bc.height == 0
        assert bc.genesis_block is not None
    
    def test_get_block(self):
        """Test getting block by hash."""
        store = MemoryStore()
        bc = Blockchain(store)
        
        block = Block(
            index=0,
            witness=Witness(b"\x00", b"\x00")
        )
        
        bc.persist(block)
        retrieved = bc.get_block(block.hash)
        assert retrieved is not None
    
    def test_contains_block(self):
        """Test contains block."""
        store = MemoryStore()
        bc = Blockchain(store)
        
        block = Block(
            index=0,
            witness=Witness(b"\x00", b"\x00")
        )
        
        bc.persist(block)
        assert bc.contains_block(block.hash)


class TestApplicationExecuted:
    """Application executed tests."""
    
    def test_create(self):
        """Test creation."""
        result = ApplicationExecuted()
        assert result.vm_state == "HALT"
        assert result.gas_consumed == 0
    
    def test_with_exception(self):
        """Test with exception."""
        result = ApplicationExecuted(
            vm_state="FAULT",
            exception="Test error"
        )
        assert result.vm_state == "FAULT"
        assert result.exception == "Test error"
