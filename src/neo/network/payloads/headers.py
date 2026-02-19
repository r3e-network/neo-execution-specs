"""Neo N3 Headers Payload."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from neo.network.payloads.header import Header

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class HeadersPayload:
    """Response payload for GetHeaders requests."""

    MAX_HEADERS_COUNT = 2000

    headers: list[Header] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.headers:
            raise ValueError("`Headers` in HeadersPayload is empty")
        if len(self.headers) > self.MAX_HEADERS_COUNT:
            raise ValueError(
                f"Headers count exceeds limit: {len(self.headers)}/{self.MAX_HEADERS_COUNT}"
            )

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_var_int(len(self.headers))
        for header in self.headers:
            header.serialize(writer)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "HeadersPayload":
        """Deserialize payload from wire format."""
        count = reader.read_var_int(cls.MAX_HEADERS_COUNT)
        headers = [Header.deserialize(reader) for _ in range(count)]
        return cls(headers=headers)
