"""
BLS12-381 Scalar field element.

The scalar field has order r where:
r = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
"""

from __future__ import annotations


# BLS12-381 scalar field modulus
SCALAR_MODULUS = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001


class Scalar:
    """Scalar field element for BLS12-381."""
    
    __slots__ = ('_value',)
    
    def __init__(self, value: int = 0) -> None:
        self._value = value % SCALAR_MODULUS
    
    @classmethod
    def from_bytes(cls, data: bytes) -> Scalar:
        """Create scalar from 32-byte little-endian representation."""
        if len(data) != 32:
            raise ValueError("Scalar must be 32 bytes")
        value = int.from_bytes(data, 'little')
        return cls(value)
    
    def to_bytes(self) -> bytes:
        """Convert to 32-byte little-endian representation."""
        return self._value.to_bytes(32, 'little')
    
    @property
    def value(self) -> int:
        return self._value
    
    def __neg__(self) -> Scalar:
        return Scalar(SCALAR_MODULUS - self._value)
    
    def __add__(self, other: Scalar) -> Scalar:
        return Scalar(self._value + other._value)
    
    def __sub__(self, other: Scalar) -> Scalar:
        return Scalar(self._value - other._value)
    
    def __mul__(self, other: Scalar) -> Scalar:
        return Scalar(self._value * other._value)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Scalar):
            return self._value == other._value
        return False
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def __repr__(self) -> str:
        return f"Scalar(0x{self._value:064x})"
    
    def is_zero(self) -> bool:
        return self._value == 0
    
    def invert(self) -> Scalar:
        """Compute multiplicative inverse."""
        if self._value == 0:
            raise ValueError("Cannot invert zero")
        return Scalar(pow(self._value, -1, SCALAR_MODULUS))
