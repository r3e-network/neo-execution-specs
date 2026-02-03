"""Tests for contract module."""

import pytest
from neo.contract import NefFile, ContractAbi


class TestNef:
    """NEF tests."""
    
    def test_checksum(self):
        """Test checksum computation."""
        nef = NefFile(script=b"\x10\x40")
        checksum = nef.compute_checksum()
        assert checksum > 0
