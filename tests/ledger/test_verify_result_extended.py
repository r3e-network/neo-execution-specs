"""Tests for verify result."""

import pytest
from neo.ledger.verify_result import VerifyResult


class TestVerifyResult:
    """Verify result tests."""
    
    def test_succeed(self):
        """Test SUCCEED result."""
        assert VerifyResult.SUCCEED == 0
    
    def test_invalid(self):
        """Test INVALID result."""
        assert VerifyResult.INVALID != 0
