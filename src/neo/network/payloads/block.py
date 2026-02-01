"""
Block - Represents a Neo N3 block.

Reference: Neo.Network.P2P.Payloads.Block
"""

from dataclasses import dataclass, field
from typing import List, Optional
from neo.types.uint256 import UInt256
from neo.network.payloads.header import Header
from neo.network.payloads.transaction import Transaction


@dataclass
class Block(Header):
    """Represents a Neo N3 block."""
    
    transactions: List[Transaction] = field(default_factory=list)
    """Transactions in the block."""
    
    @property
    def hash(self) -> UInt256:
        """Get the block hash."""
        if self._hash is None:
            from neo.crypto.hash import hash256
            self._hash = UInt256(hash256(self._get_hash_data()))
        return self._hash
    
    def _get_hash_data(self) -> bytes:
        """Get data for hash calculation."""
        data = bytearray()
        data.extend(self.version.to_bytes(4, 'little'))
        data.extend(self.prev_hash.to_bytes())
        data.extend(self.merkle_root.to_bytes())
        data.extend(self.timestamp.to_bytes(8, 'little'))
        data.extend(self.nonce.to_bytes(8, 'little'))
        data.extend(self.index.to_bytes(4, 'little'))
        data.append(self.primary_index)
        data.extend(self.next_consensus.to_bytes())
        return bytes(data)
