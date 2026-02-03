"""Tests for ContractManagement."""

import pytest
from neo.native.contract_management import ContractManagement


class TestContractManagement:
    """Test ContractManagement."""
    
    def test_name(self):
        """Test contract name."""
        cm = ContractManagement()
        assert cm.name == "ContractManagement"
