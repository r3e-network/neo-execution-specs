"""Neo N3 Key Builder."""

from typing import Union


class KeyBuilder:
    """Build storage keys."""
    
    def __init__(self, id: int, prefix: int):
        self._data = bytearray()
        self._data.extend(id.to_bytes(4, 'little'))
        self._data.append(prefix)
    
    def add(self, key: Union[bytes, int]) -> "KeyBuilder":
        """Add key component."""
        if isinstance(key, int):
            self._data.extend(key.to_bytes(4, 'little'))
        else:
            self._data.extend(key)
        return self
    
    def to_key(self) -> bytes:
        """Get final key."""
        return bytes(self._data)
