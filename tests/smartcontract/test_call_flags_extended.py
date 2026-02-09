"""Tests for call flags."""

from neo.smartcontract.call_flags import CallFlags


class TestCallFlags:
    """Call flags tests."""
    
    def test_none(self):
        """Test NONE flag."""
        assert CallFlags.NONE == 0
    
    def test_all(self):
        """Test ALL flag."""
        assert CallFlags.ALL != 0
    
    def test_read_only(self):
        """Test READ_ONLY flag."""
        assert CallFlags.READ_ONLY != 0
