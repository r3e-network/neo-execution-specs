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
        _is_compressed = (flags & 0x80) != 0  # always True for 48-byte input
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


class G1Projective:
    """G1 point in projective coordinates."""
    
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x: int = 0, y: int = 1, z: int = 0) -> None:
        self.x = x % P
        self.y = y % P
        self.z = z % P
    
    @classmethod
    def identity(cls) -> G1Projective:
        return cls(0, 1, 0)
    
    @classmethod
    def generator(cls) -> G1Projective:
        return cls.from_affine(G1Affine.generator())
    
    @classmethod
    def from_affine(cls, p: G1Affine) -> G1Projective:
        if p._is_infinity:
            return cls.identity()
        return cls(p.x, p.y, 1)
    
    def to_affine(self) -> G1Affine:
        if self.z == 0:
            return G1Affine.identity()
        # Jacobian coordinates: (x, y) = (X/Z^2, Y/Z^3)
        z_inv = pow(self.z, -1, P)
        z_inv2 = (z_inv * z_inv) % P
        z_inv3 = (z_inv2 * z_inv) % P
        x = (self.x * z_inv2) % P
        y = (self.y * z_inv3) % P
        return G1Affine(x, y)
    
    def to_compressed(self) -> bytes:
        return self.to_affine().to_compressed()
    
    def is_identity(self) -> bool:
        return self.z == 0
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, G1Projective):
            if self.z == 0 and other.z == 0:
                return True
            if self.z == 0 or other.z == 0:
                return False
            # Jacobian: affine x = X/Z², y = Y/Z³
            z1_sq = (self.z * self.z) % P
            z2_sq = (other.z * other.z) % P
            z1_cu = (z1_sq * self.z) % P
            z2_cu = (z2_sq * other.z) % P
            return (self.x * z2_sq - other.x * z1_sq) % P == 0 and \
                   (self.y * z2_cu - other.y * z1_cu) % P == 0
        if isinstance(other, G1Affine):
            return self.to_affine() == other
        return False
    
    def __neg__(self) -> G1Projective:
        return G1Projective(self.x, P - self.y, self.z)
    
    def __add__(self, other: G1Affine | G1Projective) -> G1Projective:
        if isinstance(other, G1Affine):
            other = G1Projective.from_affine(other)
        return self._add_projective(other)
    
    def _add_projective(self, other: G1Projective) -> G1Projective:
        if self.z == 0:
            return other
        if other.z == 0:
            return self
        
        # Jacobian addition formula
        z1_sq = (self.z * self.z) % P
        z2_sq = (other.z * other.z) % P
        z1_cu = (z1_sq * self.z) % P
        z2_cu = (z2_sq * other.z) % P
        
        u1 = (self.x * z2_sq) % P
        u2 = (other.x * z1_sq) % P
        s1 = (self.y * z2_cu) % P
        s2 = (other.y * z1_cu) % P
        
        if u1 == u2:
            if s1 == s2:
                return self._double()
            return G1Projective.identity()
        
        h = (u2 - u1) % P
        r = (s2 - s1) % P
        h2 = (h * h) % P
        h3 = (h2 * h) % P
        
        x3 = (r * r - h3 - 2 * u1 * h2) % P
        y3 = (r * (u1 * h2 - x3) - s1 * h3) % P
        z3 = (h * self.z * other.z) % P
        
        return G1Projective(x3, y3, z3)
    
    def _double(self) -> G1Projective:
        if self.z == 0:
            return self
        
        # Jacobian doubling formula for curve y^2 = x^3 + b (a=0)
        a = (self.x * self.x) % P
        b = (self.y * self.y) % P
        c = (b * b) % P
        
        d = (self.x + b) % P
        d = (d * d) % P
        d = (d - a - c) % P
        d = (d + d) % P  # d = 2*((X+B)^2 - A - C)
        
        e = (a + a + a) % P  # e = 3*A
        f = (e * e) % P
        
        x3 = (f - d - d) % P
        y3 = (e * (d - x3) - 8 * c) % P
        z3 = (2 * self.y * self.z) % P
        
        return G1Projective(x3, y3, z3)
    
    def __mul__(self, scalar: int | Scalar) -> G1Projective:
        if isinstance(scalar, Scalar):
            scalar = scalar.value
        scalar = scalar % SCALAR_MODULUS
        
        result = G1Projective.identity()
        temp = self
        
        while scalar > 0:
            if scalar & 1:
                result = result + temp
            temp = temp._double()
            scalar >>= 1
        
        return result
    
    def __rmul__(self, scalar: int | Scalar) -> G1Projective:
        return self * scalar


def _sqrt_mod_p(a: int) -> int | None:
    """Compute square root modulo p using Tonelli-Shanks."""
    if a == 0:
        return 0
    if pow(a, (P - 1) // 2, P) != 1:
        return None
    # For BLS12-381, p ≡ 3 (mod 4), so sqrt(a) = a^((p+1)/4)
    return pow(a, (P + 1) // 4, P)
