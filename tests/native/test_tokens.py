"""Tests for native contracts."""

from neo.native.neo_token import NeoToken
from neo.native.gas_token import GasToken


def test_neo_token():
    """Test NEO token properties."""
    neo = NeoToken()
    assert neo.symbol == "NEO"
    assert neo.decimals == 0
    assert neo.total_supply() == 100_000_000


def test_gas_token():
    """Test GAS token properties."""
    gas = GasToken()
    assert gas.symbol == "GAS"
    assert gas.decimals == 8
