"""Neo N3 UInt160 - 20-byte hash type."""

from typing import Union


class UInt160:
    """160-bit unsigned integer (20 bytes)."""
    
    ZERO: "UInt160"
    LENGTH = 20
    
    __slots__ = ('_data',)
    
    def __init__(self, data: bytes = None):
        if data is None:
            self._data = bytes(20)
        elif len(data) != 20:
            raise ValueError("UInt160 must be 20 bytes")
        else:
            self._data = bytes(data)
    
    @property
    def data(self) -> bytes:
        """Get raw bytes."""
        return self._data
    
    @classmethod
    def from_string(cls, value: str) -> "UInt160":
        """Parse from hex string."""
        if value.startswith("0x"):
            value = value[2:]
        data = bytes.fromhex(value)
        return cls(data[::-1])  # Little-endian
    
    def to_array(self) -> bytes:
        """Get as bytes."""
        return self._data
    
    def to_bytes(self) -> bytes:
        """Alias for to_array."""
        return self._data
    
    def __bytes__(self) -> bytes:
        return self._data
    
    def __str__(self) -> str:
        return "0x" + self._data[::-1].hex()
    
    def __repr__(self) -> str:
        return f"UInt160({self})"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, UInt160):
            return self._data == other._data
        return False
    
    def __hash__(self) -> int:
        return hash(self._data)
    
    def __lt__(self, other: "UInt160") -> bool:
        return self._data < other._data


UInt160.ZERO = UInt160(bytes(20))
