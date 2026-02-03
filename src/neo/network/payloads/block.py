"""
Block - Represents a Neo N3 block.

Reference: Neo.Network.P2P.Payloads.Block
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from neo.types.uint256 import UInt256
from neo.network.payloads.header import Header
from neo.network.payloads.transaction import Transaction

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class Block(Header):
    """Represents a Neo N3 block."""
    
    transactions: List[Transaction] = field(default_factory=list)
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
        from neo.io.binary_writer import BinaryWriter
        writer = BinaryWriter()
        self._serialize_unsigned(writer)
        return writer.to_bytes()
    
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the block."""
        super().serialize(writer)
        writer.write_var_int(len(self.transactions))
        for tx in self.transactions:
            tx.serialize(writer)
    
    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Block":
        """Deserialize a block."""
        header = Header.deserialize(reader)
        tx_count = reader.read_var_int(0xFFFF)
        transactions = [Transaction.deserialize(reader) for _ in range(tx_count)]
        
        return cls(
            version=header.version,
            prev_hash=header.prev_hash,
            merkle_root=header.merkle_root,
            timestamp=header.timestamp,
            nonce=header.nonce,
            index=header.index,
            primary_index=header.primary_index,
            next_consensus=header.next_consensus,
            witness=header.witness,
            transactions=transactions
        )
