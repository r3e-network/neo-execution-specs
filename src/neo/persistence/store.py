"""
Store interfaces for Neo N3 persistence.

Reference: Neo.Persistence.IStore, ISnapshot
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator


class IReadOnlyStore(ABC):
    """Read-only store interface."""

    @abstractmethod
    def get(self, key: bytes) -> bytes | None:
        """Get value by key."""
        pass

    @abstractmethod
    def contains(self, key: bytes) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def seek(self, prefix: bytes, direction: int = 1) -> Iterator[tuple[bytes, bytes]]:
        """Seek entries by prefix."""
        pass


class IStore(IReadOnlyStore):
    """Writable store interface."""

    @abstractmethod
    def put(self, key: bytes, value: bytes) -> None:
        """Put a key-value pair."""
        pass

    @abstractmethod
    def delete(self, key: bytes) -> None:
        """Delete a key."""
        pass


class ISnapshot(IStore):
    """Snapshot interface with commit."""

    @abstractmethod
    def commit(self) -> None:
        """Commit changes."""
        pass
