"""Neo N3 Inv Payload."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable

from neo.network.payloads.inventory_type import InventoryType

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter

@dataclass
class InvPayload:
    """Inventory payload."""

    MAX_HASHES_COUNT = 500

    type: int | InventoryType
    hashes: list[bytes] = field(default_factory=list)

    def __post_init__(self) -> None:
        try:
            self.type = InventoryType(self.type)
        except ValueError as exc:
            raise ValueError(f"`type`({self.type}) is not defined in InventoryType") from exc

        if len(self.hashes) > self.MAX_HASHES_COUNT:
            raise ValueError(
                f"Hashes count exceeds limit: {len(self.hashes)}/{self.MAX_HASHES_COUNT}"
            )
        for hash_value in self.hashes:
            if len(hash_value) != 32:
                raise ValueError(f"Invalid hash length: {len(hash_value)}")

    @classmethod
    def create_group(
        cls,
        inventory_type: int | InventoryType,
        hashes: Iterable[bytes],
    ) -> list["InvPayload"]:
        """Split large inventory sets into protocol-compliant payloads."""
        hash_list = list(hashes)
        return [
            cls(type=inventory_type, hashes=hash_list[i : i + cls.MAX_HASHES_COUNT])
            for i in range(0, len(hash_list), cls.MAX_HASHES_COUNT)
        ]

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_byte(int(self.type))
        writer.write_var_int(len(self.hashes))
        for hash_value in self.hashes:
            writer.write_bytes(hash_value)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "InvPayload":
        """Deserialize payload from wire format."""
        payload_type = reader.read_byte()
        hash_count = reader.read_var_int(cls.MAX_HASHES_COUNT)
        hashes = [reader.read_bytes(32) for _ in range(hash_count)]
        return cls(type=payload_type, hashes=hashes)
