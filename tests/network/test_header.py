"""Tests for Header serialization."""

from neo.network.payloads.header import Header


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
