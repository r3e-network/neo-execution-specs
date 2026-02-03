"""Tests for RoleManagement."""

import pytest
from neo.native.role_management import RoleManagement


class TestRoleManagement:
    """Test RoleManagement."""
    
    def test_name(self):
        """Test contract name."""
        rm = RoleManagement()
        assert rm.name == "RoleManagement"
