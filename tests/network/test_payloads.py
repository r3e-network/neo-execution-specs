"""Tests for network payload types."""

from neo.network.payloads.witness import Witness
from neo.network.payloads.signer import Signer
from neo.network.payloads.witness_scope import WitnessScope
from neo.types import UInt160


class TestWitness:
    """Tests for Witness type."""
    
    def test_empty_witness(self):
        """Test creating empty witness."""
        w = Witness()
        assert w.invocation_script == b''
        assert w.verification_script == b''
    
    def test_witness_with_scripts(self):
        """Test witness with scripts."""
        w = Witness(
            invocation_script=b'\x0c\x40' + b'\x00' * 64,
            verification_script=b'\x0c\x21' + b'\x00' * 33 + b'\x41'
        )
        assert len(w.invocation_script) == 66
        assert len(w.verification_script) == 36


class TestSigner:
    """Tests for Signer type."""
    
    def test_default_signer(self):
        """Test default signer."""
        account = UInt160(b'\x00' * 20)
        s = Signer(account=account)
        assert s.account == account
    
    def test_signer_with_scope(self):
        """Test signer with scope."""
        account = UInt160(b'\x01' * 20)
        s = Signer(
            account=account,
            scopes=WitnessScope.CALLED_BY_ENTRY
        )
        assert s.scopes == WitnessScope.CALLED_BY_ENTRY


class TestWitnessScope:
    """Tests for WitnessScope enum."""
    
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
