"""Tests for Header serialization."""

import pytest
from neo.network.payloads.header import Header
from neo.types.uint256 import UInt256
from neo.types.uint160 import UInt160


class TestHeader:
    """Tests for Header."""
    
    def test_default_header(self):
        """Test default header values."""
        header = Header()
        assert header.version == 0
        assert header.timestamp == 0
        assert header.nonce == 0
        assert header.index == 0
        assert header.primary_index == 0
