"""StorageKey - Keys for contract storage."""

from __future__ import annotations
from dataclasses import dataclass
import struct


@dataclass
class StorageKey:
    """Represents the keys in contract storage."""
    
    # The id of the contract.
    id: int = 0
    
    # The key of the storage entry.
    key: bytes = b""
    
    PREFIX_LENGTH = 5  # sizeof(int) + sizeof(byte)
    
    def __hash__(self) -> int:
        return hash((self.id, self.key))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, StorageKey):
            return self.id == other.id and self.key == other.key
        return False
    
    def to_array(self) -> bytes:
        """Serialize to byte array."""
        return struct.pack('<i', self.id) + self.key
    
    @classmethod
    def from_bytes(cls, data: bytes) -> StorageKey:
        """Deserialize from byte array."""
        id_val = struct.unpack('<i', data[:4])[0]
        key = data[4:]
        return cls(id=id_val, key=key)
    
    @classmethod
    def create_search_prefix(cls, id: int, prefix: bytes) -> bytes:
        """Creates a search prefix for a contract."""
        return struct.pack('<i', id) + prefix
