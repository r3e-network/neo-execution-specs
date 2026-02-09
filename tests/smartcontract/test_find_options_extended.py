"""Tests for find options."""

from neo.smartcontract.storage.find_options import FindOptions


class TestFindOptions:
    """Find options tests."""
    
    def test_none(self):
        """Test NONE option."""
        assert FindOptions.NONE == 0
    
    def test_keys_only(self):
        """Test KEYS_ONLY option."""
        assert FindOptions.KEYS_ONLY != 0
