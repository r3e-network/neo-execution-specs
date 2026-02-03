"""Tests for ledger module."""

import pytest
from neo.ledger.tx import Transaction
from neo.ledger.block import Block, BlockHeader


class TestTransaction:
    """Transaction tests."""
    
    def test_create(self):
        """Test transaction creation."""
        tx = Transaction()
        assert tx.version == 0
    
    def test_hash(self):
        """Test transaction hash."""
        tx = Transaction(script=b"\x10\x40")
        assert len(tx.hash) == 32


class TestBlock:
    """Block tests."""
    
    def test_create(self):
        """Test block creation."""
        header = BlockHeader()
        block = Block(header=header)
        assert block.index == 0
