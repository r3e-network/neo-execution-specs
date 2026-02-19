"""Neo N3 FilterLoad payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter

@dataclass
class FilterLoadPayload:
    """SPV bloom filter setup payload."""

    MAX_FILTER_BYTES = 36000
    MAX_HASH_FUNCTIONS = 50

    filter: bytes
    k: int
    tweak: int

    def __post_init__(self) -> None:
        if len(self.filter) > self.MAX_FILTER_BYTES:
            raise ValueError(
                f"Filter length exceeds limit: {len(self.filter)}/{self.MAX_FILTER_BYTES}"
            )
        if self.k < 0 or self.k > self.MAX_HASH_FUNCTIONS:
            raise ValueError(f"Invalid hash function count: {self.k}/{self.MAX_HASH_FUNCTIONS}")
        if self.tweak < 0 or self.tweak > 0xFFFFFFFF:
            raise ValueError(f"Invalid tweak: {self.tweak}")

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_var_bytes(self.filter)
        writer.write_byte(self.k)
        writer.write_uint32(self.tweak)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "FilterLoadPayload":
        """Deserialize payload from wire format."""
        return cls(
            filter=reader.read_var_bytes(cls.MAX_FILTER_BYTES),
            k=reader.read_byte(),
            tweak=reader.read_uint32(),
        )
