"""Neo N3 MerkleBlock payload."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from neo.network.payloads.header import Header

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class MerkleBlockPayload:
    """SPV merkle block payload."""

    header: Header
    tx_count: int
    hashes: list[bytes] = field(default_factory=list)
    flags: bytes = b""

    def __post_init__(self) -> None:
        if self.tx_count < 0:
            raise ValueError("Transaction count cannot be negative")

        if len(self.hashes) > self.tx_count:
            raise ValueError("Hashes count cannot exceed transaction count")

        max_flags_size = (max(self.tx_count, 1) + 7) // 8
        if len(self.flags) > max_flags_size:
            raise ValueError(
                f"Flags length exceeds limit: {len(self.flags)}/{max_flags_size}"
            )

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        self.header.serialize(writer)
        writer.write_var_int(self.tx_count)
        writer.write_var_int(len(self.hashes))
        for hash_value in self.hashes:
            if len(hash_value) != 32:
                raise ValueError(f"Invalid hash length: {len(hash_value)}")
            writer.write_bytes(hash_value)
        writer.write_var_bytes(self.flags)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "MerkleBlockPayload":
        """Deserialize payload from wire format."""
        header = Header.deserialize(reader)
        tx_count = reader.read_var_int(0xFFFF)
        hash_count = reader.read_var_int(tx_count)
        hashes = [reader.read_bytes(32) for _ in range(hash_count)]
        flags = reader.read_var_bytes((max(tx_count, 1) + 7) // 8)
        return cls(header=header, tx_count=tx_count, hashes=hashes, flags=flags)
