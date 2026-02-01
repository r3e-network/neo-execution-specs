"""
BLS12-381 G1 group elements.

G1 is the group of points on the BLS12-381 curve y^2 = x^3 + 4.
Points are represented in compressed form as 48 bytes.
"""

from __future__ import annotations
from typing import Union

from .scalar import Scalar, SCALAR_MODULUS


# BLS12-381 base field modulus
P = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab

# Curve coefficient (y^2 = x^3 + b)
B = 4


class G1Affine:
    """G1 point in affine coordinates."""
    
    __slots__ = ('x', 'y', '_is_infinity')
    
    def __init__(self, x: int = 0, y: int = 0, is_infinity: bool = False) -> None:
        self.x = x % P if not is_infinity else 0
        self.y = y % P if not is_infinity else 0
        self._is_infinity = is_infinity
    
    @classmethod
    def identity(cls) -> G1Affine:
        """Return the identity element (point at infinity)."""
        return cls(is_infinity=True)
    
    @classmethod
    def generator(cls) -> G1Affine:
        """Return the generator point."""
        # BLS12-381 G1 generator
        x = 0x17f1d3a73197d7942695638c4fa9ac0fc3688c4f9774b905a14e3a3f171bac586c55e83ff97a1aeffb3af00adb22c6bb
        y = 0x08b3f481e3aaa0f1a09e30ed741d8ae4fcf5e095d5d00af600db18cb2c04b3edd03cc744a2888ae40caa232946c5e7e1
        return cls(x, y)
    
    @classmethod
    def from_compressed(cls, data: bytes) -> G1Affine:
        """Deserialize from 48-byte compressed format."""
        if len(data) != 48:
            raise ValueError("G1 compressed point must be 48 bytes")
        
        # Check flags in first byte
        flags = data[0] & 0xe0
        is_compressed = (flags & 0x80) != 0
        is_infinity = (flags & 0x40) != 0
        is_y_odd = (flags & 0x20) != 0
        
        if is_infinity:
            return cls.identity()
        
        # Extract x coordinate
        x_bytes = bytes([data[0] & 0x1f]) + data[1:]
        x = int.from_bytes(x_bytes, 'big')
        
        if x >= P:
            raise ValueError("Invalid x coordinate")
        
        # Compute y from x: y^2 = x^3 + 4
        y_squared = (pow(x, 3, P) + B) % P
        y = _sqrt_mod_p(y_squared)
        
        if y is None:
            raise ValueError("Invalid point: not on curve")
        
        # Choose correct y based on parity
        if (y & 1) != is_y_odd:
            y = P - y
        
        return cls(x, y)
    
    def to_compressed(self) -> bytes:
        """Serialize to 48-byte compressed format."""
        if self._is_infinity:
            result = bytearray(48)
            result[0] = 0xc0  # compressed + infinity flags
            return bytes(result)
        
        x_bytes = self.x.to_bytes(48, 'big')
        result = bytearray(x_bytes)
        
        # Set flags
        result[0] |= 0x80  # compressed flag
        if self.y & 1:
            result[0] |= 0x20  # y is odd
        
        return bytes(result)
    
    def is_identity(self) -> bool:
        return self._is_infinity
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, G1Affine):
            if self._is_infinity and other._is_infinity:
                return True
            if self._is_infinity or other._is_infinity:
                return False
            return self.x == other.x and self.y == other.y
        if isinstance(other, G1Projective):
            return self == other.to_affine()
        return False
    
    def __neg__(self) -> G1Affine:
        if self._is_infinity:
            return G1Affine.identity()
        return G1Affine(self.x, P - self.y)
    
    def __add__(self, other: Union[G1Affine, G1Projective]) -> G1Projective:
        return G1Projective.from_affine(self) + other
    
    def __mul__(self, scalar: Union[int, Scalar]) -> G1Projective:
        return G1Projective.from_affine(self) * scalar
    
    def __rmul__(self, scalar: Union[int, Scalar]) -> G1Projective:
        return self * scalar


def _sqrt_mod_p(a: int) -> int | None:
    """Compute square root modulo p using Tonelli-Shanks."""
    if a == 0:
        return 0
    if pow(a, (P - 1) // 2, P) != 1:
        return None
    # For BLS12-381, p ≡ 3 (mod 4), so sqrt(a) = a^((p+1)/4)
    return pow(a, (P + 1) // 4, P)
