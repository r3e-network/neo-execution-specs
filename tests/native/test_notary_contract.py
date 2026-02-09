"""Tests for Notary."""

from neo.native.notary import Notary


class TestNotaryContract:
    """Test Notary."""
    
    def test_name(self):
        """Test contract name."""
        n = Notary()
        assert n.name == "Notary"
