"""Neo N3 Block implementation."""

from dataclasses import dataclass, field
from typing import List, Optional
import struct

from neo.crypto.hash import hash256


@dataclass
class BlockHeader:
    """Block header."""
    version: int = 0
    prev_hash: bytes = field(default_factory=lambda: bytes(32))
    merkle_root: bytes = field(default_factory=lambda: bytes(32))
    timestamp: int = 0
    nonce: int = 0
    index: int = 0
    primary_index: int = 0
    next_consensus: bytes = field(default_factory=lambda: bytes(20))
    witness: Optional["Witness"] = None
    
    _hash: Optional[bytes] = field(default=None, repr=False)
    
    @property
    def hash(self) -> bytes:
        """Get block hash."""
        if self._hash is None:
            self._hash = hash256(self._get_hash_data())
        return self._hash
    
    def _get_hash_data(self) -> bytes:
        """Get data for hashing."""
        data = bytearray()
        data.extend(struct.pack('<I', self.version))
        data.extend(self.prev_hash)
        data.extend(self.merkle_root)
        data.extend(struct.pack('<Q', self.timestamp))
        data.extend(struct.pack('<Q', self.nonce))
        data.extend(struct.pack('<I', self.index))
        data.append(self.primary_index)
        data.extend(self.next_consensus)
        return bytes(data)


@dataclass
class Block:
    """Neo N3 Block."""
    header: BlockHeader
    transactions: List = field(default_factory=list)
    
    @property
    def hash(self) -> bytes:
        return self.header.hash
    
    @property
    def index(self) -> int:
        return self.header.index
    
    @property
    def timestamp(self) -> int:
        return self.header.timestamp
