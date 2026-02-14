"""
DataCache - Caching layer for storage.

Reference: Neo.Persistence.DataCache
"""

from typing import Callable, Dict, Iterator, Optional, Tuple
from neo.persistence.store import IReadOnlyStore, IStore
from neo.persistence.track_state import TrackState


class Trackable:
    """Trackable cache entry."""
    
    def __init__(self, key: bytes, value: bytes, state: TrackState):
        self.key = key
        self.value = value
        self.state = state


class DataCache:
    """Caching layer for storage operations.
    
    Provides a write-through cache with change tracking for
    efficient batch commits to the underlying store.
    """
    
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
    
    def contains(self, key: bytes) -> bool:
        """Check if key exists."""
        if key in self._cache:
            return self._cache[key].state != TrackState.DELETED
        return self._store.contains(key)
    
    def try_get(self, key: bytes) -> Tuple[bool, Optional[bytes]]:
        """Try to get a value, returning (found, value)."""
        if key in self._cache:
            t = self._cache[key]
            if t.state == TrackState.DELETED:
                return False, None
            return True, t.value
        value = self._store.get(key)
        if value is not None:
            return True, value
        return False, None
    
    def get_or_add(self, key: bytes, factory: Callable[[], bytes]) -> bytes:
        """Get existing value or add new one using factory."""
        found, value = self.try_get(key)
        if found and value is not None:
            return value
        value = factory()
        self.add(key, value)
        return value
    
    def get_and_change(self, key: bytes, factory: Optional[Callable[[], bytes]] = None) -> Optional[bytes]:
        """Get value and mark for change, optionally creating if not exists."""
        if key in self._cache:
            t = self._cache[key]
            if t.state == TrackState.DELETED:
                if factory is None:
                    return None
                t.value = factory()
                t.state = TrackState.CHANGED
            elif t.state == TrackState.NONE:
                t.state = TrackState.CHANGED
            return t.value
        
        value = self._store.get(key)
        if value is not None:
            self._cache[key] = Trackable(key, value, TrackState.CHANGED)
            return value
        
        if factory is not None:
            value = factory()
            self._cache[key] = Trackable(key, value, TrackState.ADDED)
            return value
        return None
    
    def add(self, key: bytes, value: bytes) -> None:
        """Add a new key-value pair."""
        if key in self._cache:
            t = self._cache[key]
            if t.state != TrackState.DELETED:
                raise KeyError(f"Key already exists: {key.hex()}")
            t.value = value
            t.state = TrackState.CHANGED
        elif self._store.contains(key):
            raise KeyError(f"Key already exists: {key.hex()}")
        else:
            self._cache[key] = Trackable(key, value, TrackState.ADDED)
    
    def put(self, key: bytes, value: bytes) -> None:
        """Add or update a value."""
        if key in self._cache:
            t = self._cache[key]
            t.value = value
            if t.state == TrackState.DELETED:
                t.state = TrackState.CHANGED
            elif t.state == TrackState.NONE:
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
    
    def find(self, prefix: bytes = b"") -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with given prefix, sorted by key."""
        # Collect all matching entries (cache overrides store)
        cached_keys = set()
        results: Dict[bytes, bytes] = {}

        for key, t in self._cache.items():
            if key.startswith(prefix):
                cached_keys.add(key)
                if t.state != TrackState.DELETED:
                    results[key] = t.value

        # Merge from store (excluding cached keys)
        for key, value in self._store.seek(prefix, 1):
            if key not in cached_keys:
                results[key] = value

        # Yield sorted by key for deterministic ordering
        for key in sorted(results):
            yield key, results[key]

    def seek(self, prefix: bytes, direction: int = 1) -> Iterator[Tuple[bytes, bytes]]:
        """Seek with direction (1=forward, -1=backward)."""
        items = list(self.find(prefix))
        if direction < 0:
            items.reverse()
        yield from items
    
    def get_change_set(self) -> Iterator[Trackable]:
        """Get all changed entries."""
        for t in self._cache.values():
            if t.state != TrackState.NONE:
                yield t
    
    def commit(self) -> None:
        """Commit all changes to the underlying store."""
        if not isinstance(self._store, IStore):
            raise TypeError("Cannot commit to read-only store")
        
        for t in self._cache.values():
            if t.state == TrackState.ADDED or t.state == TrackState.CHANGED:
                self._store.put(t.key, t.value)
            elif t.state == TrackState.DELETED:
                self._store.delete(t.key)
        
        self._cache.clear()


class ClonedCache(DataCache):
    """A cloned cache that can be committed to parent cache."""
    
    def __init__(self, parent: DataCache):
        self._parent = parent
        self._cache: Dict[bytes, Trackable] = {}
    
    def get(self, key: bytes) -> Optional[bytes]:
        """Get from local cache or parent."""
        if key in self._cache:
            t = self._cache[key]
            if t.state == TrackState.DELETED:
                return None
            return t.value
        return self._parent.get(key)
    
    def contains(self, key: bytes) -> bool:
        """Check if key exists."""
        if key in self._cache:
            return self._cache[key].state != TrackState.DELETED
        return self._parent.contains(key)
    
    def put(self, key: bytes, value: bytes) -> None:
        """Add or update a value in the clone."""
        if key in self._cache:
            t = self._cache[key]
            t.value = value
            if t.state == TrackState.DELETED:
                t.state = TrackState.CHANGED
            elif t.state == TrackState.NONE:
                t.state = TrackState.CHANGED
            # ADDED state stays ADDED
        else:
            exists = self._parent.contains(key)
            state = TrackState.CHANGED if exists else TrackState.ADDED
            self._cache[key] = Trackable(key, value, state)
    
    def delete(self, key: bytes) -> None:
        """Delete a key from the clone."""
        if key in self._cache:
            t = self._cache[key]
            if t.state == TrackState.ADDED:
                del self._cache[key]
            else:
                t.state = TrackState.DELETED
        elif self._parent.contains(key):
            self._cache[key] = Trackable(key, b"", TrackState.DELETED)
    
    def find(self, prefix: bytes = b"") -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with given prefix, merging parent and local."""
        results: Dict[bytes, bytes] = {}
        # Get results from parent
        for key, value in self._parent.find(prefix):
            results[key] = value
        # Apply local changes
        for key, entry in self._cache.items():
            if key.startswith(prefix):
                if entry.state == TrackState.DELETED:
                    results.pop(key, None)
                elif entry.state in (TrackState.ADDED, TrackState.CHANGED):
                    results[key] = entry.value
        for key in sorted(results):
            yield key, results[key]

    def seek(self, prefix: bytes, direction: int = 1) -> Iterator[Tuple[bytes, bytes]]:
        """Seek with direction, merging parent and local."""
        items = list(self.find(prefix))
        if direction < 0:
            items.reverse()
        yield from items

    def commit(self) -> None:
        """Commit changes to parent cache."""
        for t in self._cache.values():
            if t.state == TrackState.ADDED:
                self._parent.add(t.key, t.value)
            elif t.state == TrackState.CHANGED:
                self._parent.put(t.key, t.value)
            elif t.state == TrackState.DELETED:
                self._parent.delete(t.key)
        self._cache.clear()
