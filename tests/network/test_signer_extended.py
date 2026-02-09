"""Extended tests for network payloads."""

from neo.network.payloads.signer import Signer
from neo.network.payloads.witness_scope import WitnessScope
from neo.types import UInt160


class TestSigner:
    """Tests for Signer class."""
    
    def test_create_default(self):
        """Test creating default signer."""
        signer = Signer()
        assert signer.account is None
        assert signer.scopes == WitnessScope.CALLED_BY_ENTRY
    
    def test_create_with_account(self):
        """Test creating signer with account."""
        account = UInt160(bytes(range(20)))
        signer = Signer(account=account)
        assert signer.account == account
    
    def test_create_with_scopes(self):
        """Test creating signer with scopes."""
        signer = Signer(scopes=WitnessScope.CALLED_BY_ENTRY)
        assert signer.scopes == WitnessScope.CALLED_BY_ENTRY
    
    def test_global_scope(self):
        """Test global scope."""
        signer = Signer(scopes=WitnessScope.GLOBAL)
        assert signer.scopes == WitnessScope.GLOBAL


class TestWitnessScope:
    """Tests for WitnessScope enum."""
    
    def test_none_scope(self):
        """Test NONE scope."""
        assert WitnessScope.NONE.value == 0
    
    def test_called_by_entry(self):
        """Test CALLED_BY_ENTRY scope."""
        assert WitnessScope.CALLED_BY_ENTRY.value == 1
    
    def test_custom_contracts(self):
        """Test CUSTOM_CONTRACTS scope."""
        assert WitnessScope.CUSTOM_CONTRACTS.value == 16
    
    def test_custom_groups(self):
        """Test CUSTOM_GROUPS scope."""
        assert WitnessScope.CUSTOM_GROUPS.value == 32
    
    def test_global_scope(self):
        """Test GLOBAL scope."""
        assert WitnessScope.GLOBAL.value == 128
