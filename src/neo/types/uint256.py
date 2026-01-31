"""UInt256 - 32-byte unsigned integer."""

from __future__ import annotations


class UInt256:
    """32-byte unsigned integer, used for hashes."""
    
    ZERO: UInt256
    LENGTH = 32
    
    __slots__ = ("_data",)
    
    def __init__(self, data: bytes = b"") -> None:
        if len(data) == 0:
            data = b"\x00" * self.LENGTH
        if len(data) != self.LENGTH:
            raise ValueError(f"UInt256 must be {self.LENGTH} bytes")
        self._data = data
    
    @property
    def data(self) -> bytes:
        return self._data
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, UInt256):
            return self._data == other._data
        return False
    
    def __hash__(self) -> int:
        return hash(self._data)
    
    def __repr__(self) -> str:
        return f"UInt256(0x{self._data.hex()})"


UInt256.ZERO = UInt256(b"\x00" * 32)
