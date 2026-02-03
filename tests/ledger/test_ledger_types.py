"""Tests for ledger types."""

import pytest
from neo.ledger.mempool import MemoryPool
from neo.ledger.verify_result import VerifyResult
from neo.ledger.tx_removal_reason import TransactionRemovalReason


class TestVerifyResult:
    """Tests for VerifyResult enum."""
    
    def test_succeed(self):
        """Test Succeed result."""
        assert VerifyResult.SUCCEED == 0
    
    def test_already_exists(self):
        """Test AlreadyExists result."""
        assert VerifyResult.ALREADY_EXISTS is not None
    
    def test_invalid(self):
        """Test Invalid result."""
        assert VerifyResult.INVALID is not None


class TestTransactionRemovalReason:
    """Tests for TransactionRemovalReason enum."""
    
    def test_added_to_block(self):
        """Test AddedToBlock reason."""
        assert TransactionRemovalReason.ADDED_TO_BLOCK == 0
    
    def test_expired(self):
        """Test Expired reason."""
        assert TransactionRemovalReason.EXPIRED == 1
    
    def test_invalid(self):
        """Test Invalid reason."""
        assert TransactionRemovalReason.INVALID == 2
