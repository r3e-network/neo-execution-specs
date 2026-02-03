"""Tests for LedgerContract."""

import pytest
from neo.native.ledger import LedgerContract


class TestLedgerContract:
    """Test LedgerContract."""
    
    def test_name(self):
        """Test contract name."""
        lc = LedgerContract()
        assert lc.name == "LedgerContract"
