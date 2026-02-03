"""Neo N3 Snapshot - Database snapshot for atomic operations.

Reference: Neo.Persistence.Snapshot
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterator, Optional, Tuple, Any
from abc import ABC, abstractmethod

from neo.persistence.store import IStore, IReadOnlyStore


class Snapshot(ABC):
    """Abstract database snapshot for atomic operations.
    
    A snapshot provides isolated read/write access to the database,
    with changes only visible after commit.
    """
    
    @abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        """Get value by key."""
        pass
    
    @abstractmethod
    def contains(self, key: bytes) -> bool:
        """Check if key exists."""
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
    def find(self, prefix: bytes) -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with prefix."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit changes."""
        pass
    
    def get_and_change(self, key: bytes, factory: Optional[Callable[[], bytes]] = None) -> Optional[bytes]:
        """Get value and mark for change."""
        value = self.get(key)
        if value is None and factory is not None:
            value = factory()
            self.put(key, value)
        return value
    
    def add(self, key: bytes, value: bytes) -> None:
        """Add new key-value pair (raises if exists)."""
        if self.contains(key):
            raise KeyError(f"Key already exists: {key.hex()}")
        self.put(key, value)


@dataclass
class MemorySnapshot(Snapshot):
    """In-memory snapshot implementation."""
    
    _store: Dict[bytes, bytes] = field(default_factory=dict)
    _changes: Dict[bytes, Optional[bytes]] = field(default_factory=dict)
    
    def get(self, key: bytes) -> Optional[bytes]:
        if key in self._changes:
            return self._changes[key]
        return self._store.get(key)
    
    def contains(self, key: bytes) -> bool:
        if key in self._changes:
            return self._changes[key] is not None
        return key in self._store
    
    def put(self, key: bytes, value: bytes) -> None:
        self._changes[key] = value
    
    def delete(self, key: bytes) -> None:
        self._changes[key] = None
    
    def find(self, prefix: bytes) -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with prefix."""
        seen = set()
        # First check changes
        for key, value in self._changes.items():
            if key.startswith(prefix):
                seen.add(key)
                if value is not None:
                    yield key, value
        # Then check store
        for key, value in sorted(self._store.items()):
            if key.startswith(prefix) and key not in seen:
                yield key, value
    
    def commit(self) -> None:
        for key, value in self._changes.items():
            if value is None:
                self._store.pop(key, None)
            else:
                self._store[key] = value
        self._changes.clear()
    
    def clone(self) -> "MemorySnapshot":
        """Create a clone of this snapshot."""
        clone = MemorySnapshot()
        clone._store = dict(self._store)
        clone._changes = dict(self._changes)
        return clone


class StoreSnapshot(Snapshot):
    """Snapshot backed by an IStore."""
    
    def __init__(self, store: IStore):
        self._store = store
        self._changes: Dict[bytes, Optional[bytes]] = {}
    
    def get(self, key: bytes) -> Optional[bytes]:
        if key in self._changes:
            return self._changes[key]
        return self._store.get(key)
    
    def contains(self, key: bytes) -> bool:
        if key in self._changes:
            return self._changes[key] is not None
        return self._store.contains(key)
    
    def put(self, key: bytes, value: bytes) -> None:
        self._changes[key] = value
    
    def delete(self, key: bytes) -> None:
        self._changes[key] = None
    
    def find(self, prefix: bytes) -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with prefix."""
        seen = set()
        for key, value in self._changes.items():
            if key.startswith(prefix):
                seen.add(key)
                if value is not None:
                    yield key, value
        for key, value in self._store.seek(prefix, 1):
            if key not in seen:
                yield key, value
    
    def commit(self) -> None:
        for key, value in self._changes.items():
            if value is None:
                self._store.delete(key)
            else:
                self._store.put(key, value)
        self._changes.clear()
