"""UInt160 - 20-byte unsigned integer."""

from __future__ import annotations
from typing import Union


class UInt160:
    """20-byte unsigned integer, used for addresses."""
    
    ZERO: UInt160
    LENGTH = 20
    
    __slots__ = ("_data",)
    
    def __init__(self, data: bytes = b"") -> None:
        if len(data) == 0:
            data = b"\x00" * self.LENGTH
        if len(data) != self.LENGTH:
            raise ValueError(f"UInt160 must be {self.LENGTH} bytes")
        self._data = data
    
    @property
    def data(self) -> bytes:
        return self._data
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, UInt160):
            return self._data == other._data
        return False
    
    def __hash__(self) -> int:
        return hash(self._data)
    
    def __repr__(self) -> str:
        return f"UInt160(0x{self._data.hex()})"
    
    def __str__(self) -> str:
        return f"0x{self._data[::-1].hex()}"


UInt160.ZERO = UInt160(b"\x00" * 20)
