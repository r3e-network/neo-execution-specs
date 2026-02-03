"""Neo N3 Storage Key."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StorageKey:
    """Storage key for contract data."""
    id: int
    key: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        return self.id.to_bytes(4, 'little') + self.key
