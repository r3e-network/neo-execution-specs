"""Tests for Block serialization."""

from neo.network.payloads.block import Block
from neo.types.uint256 import UInt256
from neo.types.uint160 import UInt160


class TestBlock:
    """Tests for Block."""
    
    def test_default_block(self):
        """Test default block values."""
        block = Block()
        assert block.version == 0
        assert block.timestamp == 0
        assert block.index == 0
        assert block.transactions == []
    
    def test_block_hash(self):
        """Test block hash calculation."""
        block = Block(
            version=0,
            prev_hash=UInt256.ZERO,
            merkle_root=UInt256.ZERO,
            timestamp=0,
            nonce=0,
            index=0,
            primary_index=0,
            next_consensus=UInt160.ZERO
        )
        h = block.hash
        assert len(h.data) == 32
