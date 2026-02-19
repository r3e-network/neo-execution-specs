"""Neo N3 FilterAdd payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter

@dataclass
class FilterAddPayload:
    """SPV bloom filter element add payload."""

    MAX_DATA_BYTES = 520

    data: bytes

    def __post_init__(self) -> None:
        if len(self.data) > self.MAX_DATA_BYTES:
            raise ValueError(f"Data length exceeds limit: {len(self.data)}/{self.MAX_DATA_BYTES}")

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_var_bytes(self.data)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "FilterAddPayload":
        """Deserialize payload from wire format."""
        return cls(data=reader.read_var_bytes(cls.MAX_DATA_BYTES))
