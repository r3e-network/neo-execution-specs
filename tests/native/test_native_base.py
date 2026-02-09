"""Tests for native contract base functionality."""

from neo.native.neo_token import NeoToken
from neo.native.gas_token import GasToken


class TestNativeContractBase:
    """Native contract base tests."""
    
    def test_neo_token_name(self):
        """Test NEO token name."""
        neo = NeoToken()
        assert neo.name == "NeoToken"
    
    def test_neo_token_symbol(self):
        """Test NEO token symbol."""
        neo = NeoToken()
        assert neo.symbol == "NEO"
    
    def test_neo_token_decimals(self):
        """Test NEO token decimals."""
        neo = NeoToken()
        assert neo.decimals == 0
    
    def test_gas_token_name(self):
        """Test GAS token name."""
        gas = GasToken()
        assert gas.name == "GasToken"
    
    def test_gas_token_symbol(self):
        """Test GAS token symbol."""
        gas = GasToken()
        assert gas.symbol == "GAS"
    
    def test_gas_token_decimals(self):
        """Test GAS token decimals."""
        gas = GasToken()
        assert gas.decimals == 8
