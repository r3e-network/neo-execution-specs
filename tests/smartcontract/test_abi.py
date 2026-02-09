"""Tests for Contract ABI."""

from neo.smartcontract.manifest.contract_abi import ContractAbi


class TestContractAbi:
    """Test ContractAbi."""
    
    def test_empty_abi(self):
        """Test empty ABI."""
        abi = ContractAbi()
        assert abi.methods == []
