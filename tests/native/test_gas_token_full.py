"""Extended tests for GasToken native contract."""

import pytest
from neo.native.gas_token import GasToken


class TestGasToken:
    """Tests for GasToken class."""
    
    def test_name(self):
        """Test token name."""
        token = GasToken()
        assert token.name == "GasToken"
    
    def test_symbol(self):
        """Test token symbol."""
        token = GasToken()
        assert token.symbol == "GAS"
    
    def test_decimals(self):
        """Test token decimals."""
        token = GasToken()
        assert token.decimals == 8
    
    def test_initial_supply(self):
        """Test initial supply calculation."""
        token = GasToken()
        # Initial GAS is 30M (52M total - 22M for NEO holders)
        assert token.total_amount == 30_000_000 * 10**8
