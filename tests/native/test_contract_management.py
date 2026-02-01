"""Tests for ContractManagement native contract."""

import pytest
from neo.native.contract_management import ContractManagement


class TestContractManagement:
    """Tests for ContractManagement."""
    
    def test_name(self):
        """Test contract name."""
        cm = ContractManagement()
        assert cm.name == "ContractManagement"
