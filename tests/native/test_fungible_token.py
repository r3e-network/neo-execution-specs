"""Tests for FungibleToken."""

from neo.native.neo_token import NeoToken


class TestFungibleToken:
    """Test FungibleToken base."""
    
    def test_symbol(self):
        """Test symbol."""
        neo = NeoToken()
        assert neo.symbol == "NEO"
    
    def test_decimals(self):
        """Test decimals."""
        neo = NeoToken()
        assert neo.decimals == 0
