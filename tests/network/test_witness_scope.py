"""Tests for WitnessScope enum."""

from neo.network.payloads.witness_scope import WitnessScope


class TestWitnessScope:
    """Tests for WitnessScope."""
    
    def test_none_scope(self):
        """Test None scope."""
        assert WitnessScope.NONE == 0
    
    def test_called_by_entry(self):
        """Test CalledByEntry scope."""
        assert WitnessScope.CALLED_BY_ENTRY == 0x01
    
    def test_custom_contracts(self):
        """Test CustomContracts scope."""
        assert WitnessScope.CUSTOM_CONTRACTS == 0x10
    
    def test_custom_groups(self):
        """Test CustomGroups scope."""
        assert WitnessScope.CUSTOM_GROUPS == 0x20
    
    def test_global_scope(self):
        """Test Global scope."""
        assert WitnessScope.GLOBAL == 0x80
    
    def test_scope_combination(self):
        """Test combining scopes."""
        combined = WitnessScope.CALLED_BY_ENTRY | WitnessScope.CUSTOM_CONTRACTS
        assert combined & WitnessScope.CALLED_BY_ENTRY
        assert combined & WitnessScope.CUSTOM_CONTRACTS
