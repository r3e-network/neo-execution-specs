"""Neo N3 Cloned Cache - Cached data access."""

from typing import Dict, Optional, Generic, TypeVar

T = TypeVar('T')


class ClonedCache(Generic[T]):
    """Cached data with change tracking."""
    
    def __init__(self):
        self._inner: Dict[bytes, T] = {}
        self._changed: Dict[bytes, T] = {}
        self._deleted: set = set()
    
    def get(self, key: bytes) -> Optional[T]:
        """Get item."""
        if key in self._deleted:
            return None
        if key in self._changed:
            return self._changed[key]
        return self._inner.get(key)
    
    def add(self, key: bytes, value: T) -> None:
        """Add item."""
        self._deleted.discard(key)
        self._changed[key] = value
    
    def delete(self, key: bytes) -> None:
        """Delete item."""
        self._changed.pop(key, None)
        self._deleted.add(key)
    
    def commit(self) -> None:
        """Commit changes."""
        for key in self._deleted:
            self._inner.pop(key, None)
        self._inner.update(self._changed)
        self._changed.clear()
        self._deleted.clear()
