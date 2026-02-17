"""
In-memory store implementation.

Reference: Neo.Persistence.Providers.MemoryStore
"""

from collections.abc import Iterator
from typing import Dict, Optional, Tuple

from neo.persistence.store import IStore


class MemoryStore(IStore):
    """In-memory key-value store."""
    
    def __init__(self):
        self._data: Dict[bytes, bytes] = {}
    
    def get(self, key: bytes) -> Optional[bytes]:
        return self._data.get(key)
    
    def contains(self, key: bytes) -> bool:
        return key in self._data
    
    def seek(
        self,
        prefix: bytes,
        direction: int = 1
    ) -> Iterator[Tuple[bytes, bytes]]:
        """Seek with prefix filtering and direction.

        direction > 0 (Forward): ascending key order
        direction < 0 (Backward): descending key order
        """
        items = sorted(self._data.items())
        if direction < 0:
            # Backward: entries with matching prefix in descending key order
            result = [(k, v) for k, v in items if k.startswith(prefix)]
            for k, v in reversed(result):
                yield k, v
        else:
            # Forward: entries with matching prefix in ascending key order
            for k, v in items:
                if k.startswith(prefix):
                    yield k, v
    
    def put(self, key: bytes, value: bytes) -> None:
        self._data[key] = value
    
    def delete(self, key: bytes) -> None:
        self._data.pop(key, None)
