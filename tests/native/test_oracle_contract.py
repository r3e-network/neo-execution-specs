"""Tests for Oracle."""

from neo.native.oracle import OracleContract


class TestOracleContract:
    """Test OracleContract."""
    
    def test_name(self):
        """Test contract name."""
        o = OracleContract()
        assert o.name == "OracleContract"
