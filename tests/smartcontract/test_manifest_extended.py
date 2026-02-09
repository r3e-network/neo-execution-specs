"""Tests for contract manifest."""

from neo.smartcontract.manifest.contract_manifest import ContractManifest
from neo.smartcontract.manifest.contract_abi import ContractAbi


class TestContractManifest:
    """Contract manifest tests."""
    
    def test_create_manifest(self):
        """Test manifest creation."""
        manifest = ContractManifest(name="TestContract")
        assert manifest.name == "TestContract"
    
    def test_manifest_with_abi(self):
        """Test manifest with ABI."""
        abi = ContractAbi()
        manifest = ContractManifest(name="TestContract", abi=abi)
        assert manifest.abi is not None
