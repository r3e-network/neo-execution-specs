"""Extended tests for GasToken native contract."""

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

    def test_initial_gas_constant(self):
        """Test initial GAS constant."""
        # Initial GAS is 52M (C# ProtocolSettings.InitialGasDistribution)
        assert GasToken.INITIAL_GAS == 52_000_000 * 10**8

    def test_factor(self):
        """Test GAS factor (decimals)."""
        token = GasToken()
        assert token.factor == 10**8
