"""StorageContext - Context for storage operations."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class StorageContext:
    """The storage context used to read and write data in smart contracts."""
    
    # The id of the contract that owns the context.
    id: int = 0
    
    # Indicates whether the context is read-only.
    is_read_only: bool = False
    
    def as_read_only(self) -> StorageContext:
        """Convert to a read-only context."""
        if self.is_read_only:
            return self
        return StorageContext(id=self.id, is_read_only=True)
