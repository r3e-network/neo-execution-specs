"""Tests for Ledger native contract."""

import pytest
from neo.native.ledger import LedgerContract


class TestLedgerContract:
    """Tests for LedgerContract."""
    
    def test_name(self):
        """Test contract name."""
        ledger = LedgerContract()
        assert ledger.name == "LedgerContract"
