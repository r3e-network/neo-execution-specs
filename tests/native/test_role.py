"""Tests for Role."""

from neo.native.role import Role


class TestRole:
    """Role tests."""
    
    def test_roles(self):
        """Test role values."""
        assert Role.ORACLE == 8
