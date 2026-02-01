"""Tests for Blockchain."""

import pytest
from neo.ledger.blockchain import Blockchain, ApplicationExecuted
from neo.network.payloads.block import Block
from neo.persistence.memory_store import MemoryStore


class TestBlockchain:
    """Test cases for Blockchain."""
    
    def test_initial_state(self):
        """Test initial blockchain state."""
        store = MemoryStore()
        bc = Blockchain(store)
        
        assert bc.height == -1
        assert bc.current_block is None
        assert bc.genesis_block is None
    
    def test_persist_genesis(self):
        """Test persisting genesis block."""
        store = MemoryStore()
        bc = Blockchain(store)
        block = Block(index=0)
        
        bc.persist(block)
        
        assert bc.height == 0
        assert bc.genesis_block == block
        assert bc.current_block == block
    
    def test_get_block(self):
        """Test getting block by hash."""
        store = MemoryStore()
        bc = Blockchain(store)
        block = Block(index=0)
        
        bc.persist(block)
        
        result = bc.get_block(block.hash)
        assert result == block
    
    def test_contains_block(self):
        """Test contains_block method."""
        store = MemoryStore()
        bc = Blockchain(store)
        block = Block(index=0)
        
        assert not bc.contains_block(block.hash)
        bc.persist(block)
        assert bc.contains_block(block.hash)
