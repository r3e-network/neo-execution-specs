"""Extended tests for ledger components."""

import pytest
from neo.ledger.verify_result import VerifyResult
from neo.ledger.tx_removal_reason import TransactionRemovalReason


class TestVerifyResult:
    """Tests for VerifyResult enum."""
    
    def test_succeed(self):
        """Test SUCCEED result."""
        assert VerifyResult.SUCCEED.value == 0
    
    def test_already_exists(self):
        """Test ALREADY_EXISTS result."""
        assert VerifyResult.ALREADY_EXISTS.value == 1
    
    def test_already_in_pool(self):
        """Test ALREADY_IN_POOL result."""
        assert VerifyResult.ALREADY_IN_POOL.value == 2
    
    def test_out_of_memory(self):
        """Test OUT_OF_MEMORY result."""
        assert VerifyResult.OUT_OF_MEMORY.value == 3
    
    def test_unable_to_verify(self):
        """Test UNABLE_TO_VERIFY result."""
        assert VerifyResult.UNABLE_TO_VERIFY.value == 4
    
    def test_invalid(self):
        """Test INVALID result."""
        assert VerifyResult.INVALID.value == 5
    
    def test_expired(self):
        """Test EXPIRED result."""
        assert VerifyResult.EXPIRED.value == 10
    
    def test_unknown(self):
        """Test UNKNOWN result."""
        assert VerifyResult.UNKNOWN.value == 14


class TestTransactionRemovalReason:
    """Tests for TransactionRemovalReason enum."""
    
    def test_added_to_block(self):
        """Test ADDED_TO_BLOCK reason."""
        assert TransactionRemovalReason.ADDED_TO_BLOCK.value == 0
    
    def test_expired(self):
        """Test EXPIRED reason."""
        assert TransactionRemovalReason.EXPIRED.value == 1
    
    def test_invalid(self):
        """Test INVALID reason."""
        assert TransactionRemovalReason.INVALID.value == 2
