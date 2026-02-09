"""Tests for CallFlags."""

from neo.smartcontract.call_flags import CallFlags


class TestCallFlags:
    """Test CallFlags."""
    
    def test_all(self):
        """Test ALL flag."""
        assert CallFlags.ALL is not None
