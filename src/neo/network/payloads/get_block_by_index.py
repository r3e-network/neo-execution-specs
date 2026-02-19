"""Neo N3 GetBlockByIndex Payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from neo.network.payloads.headers import HeadersPayload

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class GetBlockByIndexPayload:
    """GetBlockByIndex request payload."""

    index_start: int
    count: int = -1

    def __post_init__(self) -> None:
        if self.index_start < 0 or self.index_start > 0xFFFFFFFF:
            raise ValueError(f"Invalid index_start: {self.index_start}")

        # Neo v3.9.1 allows -1 (as many as possible) or [1, MaxHeadersCount].
        if self.count == -1:
            return
        if self.count == 0 or self.count < -1 or self.count > HeadersPayload.MAX_HEADERS_COUNT:
            raise ValueError(
                f"Invalid count: {self.count}/{HeadersPayload.MAX_HEADERS_COUNT}."
            )

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_uint32(self.index_start)
        writer.write_int16(self.count)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "GetBlockByIndexPayload":
        """Deserialize payload from wire format."""
        return cls(
            index_start=reader.read_uint32(),
            count=reader.read_int16(),
        )
