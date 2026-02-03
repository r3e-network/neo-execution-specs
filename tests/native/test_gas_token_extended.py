"""Tests for GasToken."""

import pytest
from neo.native.gas_token import GasToken


class TestGasTokenExtended:
    """Test GasToken."""
    
    def test_symbol(self):
        """Test symbol."""
        gas = GasToken()
        assert gas.symbol == "GAS"
    
    def test_decimals(self):
        """Test decimals."""
        gas = GasToken()
        assert gas.decimals == 8
