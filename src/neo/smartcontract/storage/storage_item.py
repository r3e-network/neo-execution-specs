"""StorageItem - Values in contract storage."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class StorageItem:
    """Represents the values in contract storage."""
    
    _value: bytes = field(default=b"")
    _cache: Optional[Any] = field(default=None, repr=False)
    
    @property
    def value(self) -> bytes:
        """Get the byte array value."""
        if self._value:
            return self._value
        if self._cache is not None:
            if isinstance(self._cache, int):
                # Convert integer to bytes
                if self._cache == 0:
                    return b""
                length = (self._cache.bit_length() + 8) // 8
                return self._cache.to_bytes(length, 'little', signed=True)
        return b""
    
    @value.setter
    def value(self, val: bytes) -> None:
        """Set the byte array value."""
        self._value = val
        self._cache = None
    
    def get_integer(self) -> int:
        """Get value as integer."""
        if self._cache is not None and isinstance(self._cache, int):
            return self._cache
        if not self._value:
            return 0
        return int.from_bytes(self._value, 'little', signed=True)
    
    def set_integer(self, value: int) -> None:
        """Set value as integer."""
        self._cache = value
        self._value = b""
    
    def add(self, value: int) -> None:
        """Add to integer value."""
        self.set_integer(self.get_integer() + value)
    
    def clone(self) -> StorageItem:
        """Create a copy of this item."""
        return StorageItem(_value=self._value, _cache=self._cache)
