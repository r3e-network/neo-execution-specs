"""Tests for contract module."""

from neo.contract import NefFile


class TestNef:
    """NEF tests."""
    
    def test_checksum(self):
        """Test checksum computation."""
        nef = NefFile(script=b"\x10\x40")
        checksum = nef.compute_checksum()
        assert checksum > 0
