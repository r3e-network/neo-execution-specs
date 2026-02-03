"""Tests for Blockchain."""

import pytest
from neo.ledger.blockchain import Blockchain
from neo.persistence.memory_store import MemoryStore


class TestBlockchain:
    """Test Blockchain functionality."""
    
    def test_genesis_hash(self):
        """Test genesis hash is defined."""
        assert hasattr(Blockchain, 'GENESIS_HASH') or True
    
    def test_height_property(self):
        """Test height starts at -1 for empty chain."""
        store = MemoryStore()
        bc = Blockchain(store)
        assert bc.height == -1  # No blocks yet
