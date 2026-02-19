"""Neo N3 GetBlocks Payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class GetBlocksPayload:
    """GetBlocks request."""

    MAX_COUNT = 0x7FFF

    hash_start: bytes
    count: int = -1

    def __post_init__(self) -> None:
        if len(self.hash_start) != 32:
            raise ValueError(f"Invalid hash_start length: {len(self.hash_start)}")
        if self.count < -1 or self.count == 0:
            raise ValueError(f"Invalid count: {self.count}.")
        if self.count > self.MAX_COUNT:
            raise ValueError(f"Count exceeds int16 range: {self.count}/{self.MAX_COUNT}.")

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_bytes(self.hash_start)
        writer.write_int16(self.count)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "GetBlocksPayload":
        """Deserialize payload from wire format."""
        return cls(
            hash_start=reader.read_bytes(32),
            count=reader.read_int16(),
        )
