"""KeyBuilder - Build storage keys for native contracts."""

from __future__ import annotations
import struct


class KeyBuilder:
    """Used to build storage keys for native contracts."""
    
    PREFIX_LENGTH = 5  # sizeof(int) + sizeof(byte)
    
    def __init__(self, id: int, prefix: int, max_length: int = 64) -> None:
        """Initialize KeyBuilder.
        
        Args:
            id: The contract id.
            prefix: The key prefix byte.
            max_length: Maximum key length (excluding id and prefix).
        """
        if max_length < 0:
            raise ValueError("max_length must be >= 0")
        
        self._data = bytearray(max_length + self.PREFIX_LENGTH)
        struct.pack_into('<i', self._data, 0, id)
        self._data[4] = prefix
        self._length = self.PREFIX_LENGTH
    
    def add_byte(self, key: int) -> KeyBuilder:
        """Add a single byte to the key."""
        self._check_length(1)
        self._data[self._length] = key & 0xFF
        self._length += 1
        return self
    
    def add(self, key: bytes) -> KeyBuilder:
        """Add bytes to the key."""
        self._check_length(len(key))
        self._data[self._length:self._length + len(key)] = key
        self._length += len(key)
        return self
    
    def add_big_endian_int(self, key: int) -> KeyBuilder:
        """Add 32-bit integer in big-endian."""
        self._check_length(4)
        struct.pack_into('>i', self._data, self._length, key)
        self._length += 4
        return self
    
    def add_big_endian_uint(self, key: int) -> KeyBuilder:
        """Add 32-bit unsigned integer in big-endian."""
        self._check_length(4)
        struct.pack_into('>I', self._data, self._length, key)
        self._length += 4
        return self
    
    def add_big_endian_long(self, key: int) -> KeyBuilder:
        """Add 64-bit integer in big-endian."""
        self._check_length(8)
        struct.pack_into('>q', self._data, self._length, key)
        self._length += 8
        return self
    
    def _check_length(self, length: int) -> None:
        """Check if there's enough space."""
        if self._length + length > len(self._data):
            raise OverflowError("Input data too large!")
    
    def to_array(self) -> bytes:
        """Get the built key as bytes."""
        return bytes(self._data[:self._length])
