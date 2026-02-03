"""Neo N3 Header.

Reference: Neo.Network.P2P.Payloads.Header
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter
    from neo.types import UInt256, UInt160


# Header size without witness
HEADER_SIZE = 4 + 32 + 32 + 8 + 8 + 4 + 1 + 20 + 1


@dataclass
class Header:
    """Block header containing metadata."""
    version: int = 0
    prev_hash: bytes = field(default_factory=lambda: bytes(32))
    merkle_root: bytes = field(default_factory=lambda: bytes(32))
    timestamp: int = 0
    nonce: int = 0
    index: int = 0
    primary_index: int = 0
    next_consensus: bytes = field(default_factory=lambda: bytes(20))
    witness: Optional["Witness"] = None
    
    @property
    def hash(self) -> bytes:
        """Get the header hash."""
        from neo.crypto.hash import hash256
        return hash256(self._get_hash_data())
    
    def _get_hash_data(self) -> bytes:
        """Get data for hash calculation."""
        from neo.io.binary_writer import BinaryWriter
        writer = BinaryWriter()
        self._serialize_unsigned(writer)
        return writer.to_bytes()
    
    def _serialize_unsigned(self, writer: "BinaryWriter") -> None:
        """Serialize unsigned header data."""
        writer.write_uint32(self.version)
        # Handle both bytes and UInt256/UInt160
        prev = self.prev_hash.data if hasattr(self.prev_hash, 'data') else self.prev_hash
        merkle = self.merkle_root.data if hasattr(self.merkle_root, 'data') else self.merkle_root
        next_cons = self.next_consensus.data if hasattr(self.next_consensus, 'data') else self.next_consensus
        writer.write_bytes(prev)
        writer.write_bytes(merkle)
        writer.write_uint64(self.timestamp)
        writer.write_uint64(self.nonce)
        writer.write_uint32(self.index)
        writer.write_byte(self.primary_index)
        writer.write_bytes(next_cons)
    
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the header."""
        self._serialize_unsigned(writer)
        writer.write_byte(1)  # Witness count
        if self.witness:
            self.witness.serialize(writer)
        else:
            from neo.network.payloads.witness import Witness
            Witness.empty().serialize(writer)
    
    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Header":
        """Deserialize a header."""
        from neo.network.payloads.witness import Witness
        
        version = reader.read_uint32()
        prev_hash = reader.read_bytes(32)
        merkle_root = reader.read_bytes(32)
        timestamp = reader.read_uint64()
        nonce = reader.read_uint64()
        index = reader.read_uint32()
        primary_index = reader.read_byte()
        next_consensus = reader.read_bytes(20)
        
        witness_count = reader.read_byte()
        witness = Witness.deserialize(reader) if witness_count > 0 else None
        
        return cls(
            version=version,
            prev_hash=prev_hash,
            merkle_root=merkle_root,
            timestamp=timestamp,
            nonce=nonce,
            index=index,
            primary_index=primary_index,
            next_consensus=next_consensus,
            witness=witness
        )
