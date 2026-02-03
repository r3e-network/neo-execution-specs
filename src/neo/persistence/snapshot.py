"""Neo N3 Snapshot - Database snapshot for atomic operations."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


class Snapshot(ABC):
    """Abstract database snapshot."""
    
    @abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        """Get value by key."""
        pass
    
    @abstractmethod
    def put(self, key: bytes, value: bytes) -> None:
        """Put key-value pair."""
        pass
    
    @abstractmethod
    def delete(self, key: bytes) -> None:
        """Delete key."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit changes."""
        pass


@dataclass
class MemorySnapshot(Snapshot):
    """In-memory snapshot implementation."""
    
    _store: Dict[bytes, bytes] = field(default_factory=dict)
    _changes: Dict[bytes, Optional[bytes]] = field(default_factory=dict)
    
    def get(self, key: bytes) -> Optional[bytes]:
        if key in self._changes:
            return self._changes[key]
        return self._store.get(key)
    
    def put(self, key: bytes, value: bytes) -> None:
        self._changes[key] = value
    
    def delete(self, key: bytes) -> None:
        self._changes[key] = None
    
    def commit(self) -> None:
        for key, value in self._changes.items():
            if value is None:
                self._store.pop(key, None)
            else:
                self._store[key] = value
        self._changes.clear()
