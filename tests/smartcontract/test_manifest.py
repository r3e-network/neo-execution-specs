"""Tests for contract manifest types."""

import pytest
from neo.smartcontract.manifest.contract_abi import ContractAbi
from neo.smartcontract.manifest.contract_manifest import ContractManifest
from neo.smartcontract.manifest.contract_group import ContractGroup
from neo.smartcontract.manifest.contract_permission import ContractPermission


class TestContractAbi:
    """Tests for ContractAbi."""
    
    def test_create_empty(self):
        """Test creating empty ABI."""
        abi = ContractAbi()
        assert abi is not None
    
    def test_methods_list(self):
        """Test methods list."""
        abi = ContractAbi()
        assert hasattr(abi, 'methods')


class TestContractManifest:
    """Tests for ContractManifest."""
    
    def test_create_empty(self):
        """Test creating empty manifest."""
        manifest = ContractManifest()
        assert manifest is not None
    
    def test_has_name(self):
        """Test manifest has name attribute."""
        manifest = ContractManifest()
        assert hasattr(manifest, 'name')


class TestContractGroup:
    """Tests for ContractGroup."""
    
    def test_create(self):
        """Test creating contract group."""
        group = ContractGroup()
        assert group is not None


class TestContractPermission:
    """Tests for ContractPermission."""
    
    def test_create(self):
        """Test creating contract permission."""
        perm = ContractPermission()
        assert perm is not None
