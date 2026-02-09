"""Tests for Account module."""

from neo.wallets.account import (
    AccountType,
    Contract,
    ContractParameter,
)


class TestAccountType:
    """Tests for AccountType enum."""
    
    def test_standard(self):
        """Test STANDARD value."""
        assert AccountType.STANDARD == 0
    
    def test_multi_sig(self):
        """Test MULTI_SIG value."""
        assert AccountType.MULTI_SIG == 1
    
    def test_contract(self):
        """Test CONTRACT value."""
        assert AccountType.CONTRACT == 2


class TestContractParameter:
    """Tests for ContractParameter."""
    
    def test_creation(self):
        """Test parameter creation."""
        param = ContractParameter("sig", "Signature")
        assert param.name == "sig"
        assert param.type == "Signature"


class TestContract:
    """Tests for Contract."""
    
    def test_creation(self):
        """Test contract creation."""
        contract = Contract(script=b'\x10\x40')
        assert contract.script == b'\x10\x40'
        assert contract.parameters == []
        assert contract.deployed is False
