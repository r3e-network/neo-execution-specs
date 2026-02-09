"""Tests for Wallet."""

from neo.wallets.wallet import Wallet


class TestWallet:
    """Test Wallet."""
    
    def test_create(self):
        """Test create."""
        w = Wallet()
        assert w is not None
