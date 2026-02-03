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
    
    _hash: Optional[UInt256] = field(default=None, repr=False)
    
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
        # Handle both bytes and UInt256
        if hasattr(self.prev_hash, 'to_bytes'):
            data.extend(self.prev_hash.to_bytes())
        else:
            data.extend(self.prev_hash)
        if hasattr(self.merkle_root, 'to_bytes'):
            data.extend(self.merkle_root.to_bytes())
        else:
            data.extend(self.merkle_root)
        data.extend(self.timestamp.to_bytes(8, 'little'))
        data.extend(self.nonce.to_bytes(8, 'little'))
        data.extend(self.index.to_bytes(4, 'little'))
        data.append(self.primary_index)
        if hasattr(self.next_consensus, 'to_bytes'):
            data.extend(self.next_consensus.to_bytes())
        else:
            data.extend(self.next_consensus)
        return bytes(data)
