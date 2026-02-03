"""Neo N3 UInt256 - 32-byte hash type."""


class UInt256:
    """256-bit unsigned integer (32 bytes)."""
    
    ZERO: "UInt256"
    LENGTH = 32
    
    __slots__ = ('_data',)
    
    def __init__(self, data: bytes = None):
        if data is None:
            self._data = bytes(32)
        elif len(data) != 32:
            raise ValueError("UInt256 must be 32 bytes")
        else:
            self._data = bytes(data)
    
    @property
    def data(self) -> bytes:
        """Get raw bytes."""
        return self._data
    
    @classmethod
    def from_string(cls, value: str) -> "UInt256":
        """Parse from hex string."""
        if value.startswith("0x"):
            value = value[2:]
        data = bytes.fromhex(value)
        return cls(data[::-1])
    
    def to_array(self) -> bytes:
        return self._data
    
    def to_bytes(self) -> bytes:
        """Alias for to_array."""
        return self._data
    
    def __bytes__(self) -> bytes:
        return self._data
    
    def __str__(self) -> str:
        return "0x" + self._data[::-1].hex()
    
    def __eq__(self, other) -> bool:
        if isinstance(other, UInt256):
            return self._data == other._data
        return False
    
    def __hash__(self) -> int:
        return hash(self._data)


UInt256.ZERO = UInt256(bytes(32))
