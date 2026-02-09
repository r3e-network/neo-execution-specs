"""Tests for Header serialization."""

from neo.network.payloads.header import Header
from neo.network.payloads.witness import Witness


class TestHeaderSerialization:
    """Test Header serialization."""
    
    def test_default_header(self):
        """Test default header values."""
        h = Header()
        assert h.version == 0
        assert h.index == 0
        assert h.primary_index == 0
    
    def test_header_hash(self):
        """Test header hash calculation."""
        h = Header(
            version=0,
            prev_hash=bytes(32),
            merkle_root=bytes(32),
            timestamp=1234567890,
            nonce=0,
            index=1,
            primary_index=0,
            next_consensus=bytes(20)
        )
        hash_val = h.hash
        assert len(hash_val) == 32
    
    def test_header_with_witness(self):
        """Test header with witness."""
        h = Header(
            witness=Witness(b"\x01", b"\x02")
        )
        assert h.witness is not None
        assert h.witness.invocation_script == b"\x01"
