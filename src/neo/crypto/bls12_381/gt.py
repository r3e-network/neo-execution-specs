"""
BLS12-381 Gt group element.

Gt is the target group of the pairing, a subgroup of Fp12*.
Elements are represented as 576 bytes.
"""

from __future__ import annotations
from typing import Union

from .scalar import Scalar, SCALAR_MODULUS


# BLS12-381 base field modulus
P = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab


class Gt:
    """Element of the target group Gt (subgroup of Fp12*)."""
    
    __slots__ = ('_data',)
    
    def __init__(self, data: bytes = None) -> None:
        """Initialize Gt element from 576-byte representation."""
        if data is None:
            # Identity element
            self._data = self._identity_bytes()
        else:
            if len(data) != 576:
                raise ValueError("Gt element must be 576 bytes")
            self._data = bytes(data)
    
    @classmethod
    def identity(cls) -> Gt:
        """Return the identity element (1 in multiplicative notation)."""
        return cls()
    
    @staticmethod
    def _identity_bytes() -> bytes:
        """Return bytes for identity element."""
        # Identity in Fp12 is 1
        result = bytearray(576)
        # Set c0.c0.c0 = 1 (first 48 bytes)
        result[47] = 1
        return bytes(result)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> Gt:
        """Deserialize from 576-byte representation."""
        return cls(data)
    
    def to_bytes(self) -> bytes:
        """Serialize to 576-byte representation."""
        return self._data
    
    def to_array(self) -> bytes:
        """Alias for to_bytes()."""
        return self._data
    
    def is_identity(self) -> bool:
        """Check if this is the identity element."""
        return self._data == self._identity_bytes()
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Gt):
            return self._data == other._data
        return False
    
    def __hash__(self) -> int:
        return hash(self._data)
    
    def __mul__(self, other: Gt) -> Gt:
        """Multiply two Gt elements (group operation)."""
        # Simplified: XOR for placeholder
        # Real implementation requires Fp12 multiplication
        result = bytearray(576)
        for i in range(576):
            result[i] = self._data[i] ^ other._data[i]
        return Gt(bytes(result))
    
    def __add__(self, other: Gt) -> Gt:
        """Add in additive notation (same as multiply)."""
        return self * other
    
    def __pow__(self, scalar: int) -> Gt:
        """Exponentiation by scalar."""
        if isinstance(scalar, Scalar):
            scalar = scalar.value
        scalar = scalar % SCALAR_MODULUS
        
        if scalar == 0:
            return Gt.identity()
        if scalar == 1:
            return self
        
        result = Gt.identity()
        temp = self
        
        while scalar > 0:
            if scalar & 1:
                result = result * temp
            temp = temp * temp
            scalar >>= 1
        
        return result
    
    def __repr__(self) -> str:
        return f"Gt({self._data[:8].hex()}...)"
