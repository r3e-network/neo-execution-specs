"""
DataCache - Caching layer for storage.

Reference: Neo.Persistence.DataCache
"""

from enum import Enum
from typing import Dict, Iterator, Optional, Tuple
from neo.persistence.store import IReadOnlyStore


class TrackState(Enum):
    """Track state for cached items."""
    NONE = 0
    ADDED = 1
    CHANGED = 2
    DELETED = 3


class Trackable:
    """Trackable cache entry."""
    
    def __init__(self, key: bytes, value: bytes, state: TrackState):
        self.key = key
        self.value = value
        self.state = state


class DataCache:
    """Caching layer for storage operations."""
    
    def __init__(self, store: IReadOnlyStore):
        self._store = store
        self._cache: Dict[bytes, Trackable] = {}
    
    def get(self, key: bytes) -> Optional[bytes]:
        """Get value from cache or store."""
        if key in self._cache:
            t = self._cache[key]
            if t.state == TrackState.DELETED:
                return None
            return t.value
        return self._store.get(key)
    
    def put(self, key: bytes, value: bytes) -> None:
        """Add or update a value."""
        if key in self._cache:
            t = self._cache[key]
            t.value = value
            if t.state == TrackState.DELETED:
                t.state = TrackState.CHANGED
        else:
            exists = self._store.contains(key)
            state = TrackState.CHANGED if exists else TrackState.ADDED
            self._cache[key] = Trackable(key, value, state)
    
    def delete(self, key: bytes) -> None:
        """Delete a key."""
        if key in self._cache:
            t = self._cache[key]
            if t.state == TrackState.ADDED:
                del self._cache[key]
            else:
                t.state = TrackState.DELETED
        elif self._store.contains(key):
            self._cache[key] = Trackable(key, b"", TrackState.DELETED)
