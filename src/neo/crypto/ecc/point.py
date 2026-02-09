"""
Elliptic Curve Point.

Reference: Neo.Cryptography.ECC.ECPoint
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.crypto.ecc.curve import ECCurve


@dataclass
class ECPoint:
    """Point on an elliptic curve."""
    x: int
    y: int
    curve: "ECCurve"
    
    @property
    def is_infinity(self) -> bool:
        """Check if this is the point at infinity."""
        return self.x == 0 and self.y == 0
    
    def encode(self, compressed: bool = True) -> bytes:
        """Encode point to bytes."""
        if self.is_infinity:
            return b"\x00"
        
        x_bytes = self.x.to_bytes(32, 'big')
        
        if compressed:
            prefix = 0x02 if self.y % 2 == 0 else 0x03
            return bytes([prefix]) + x_bytes
        else:
            y_bytes = self.y.to_bytes(32, 'big')
            return b"\x04" + x_bytes + y_bytes
    
    @classmethod
    def decode(cls, data: bytes, curve: "ECCurve") -> "ECPoint":
        """Decode point from bytes."""
        if len(data) == 0 or data[0] == 0x00:
            return cls(0, 0, curve)
        
        if data[0] == 0x04:  # Uncompressed
            x = int.from_bytes(data[1:33], 'big')
            y = int.from_bytes(data[33:65], 'big')
            if not cls._is_on_curve(x, y, curve):
                raise ValueError("Invalid point: not on curve")
            return cls(x, y, curve)
        
        if data[0] in (0x02, 0x03):  # Compressed
            x = int.from_bytes(data[1:33], 'big')
            y = cls._decompress_y(x, data[0] == 0x03, curve)
            return cls(x, y, curve)
        
        raise ValueError(f"Invalid point encoding: {data[0]:#x}")
    
    @staticmethod
    def _is_on_curve(x: int, y: int, curve: "ECCurve") -> bool:
        """Verify that (x, y) satisfies y² = x³ + ax + b (mod p)."""
        p = curve.p
        lhs = pow(y, 2, p)
        rhs = (pow(x, 3, p) + curve.a * x + curve.b) % p
        return lhs == rhs

    @staticmethod
    def _decompress_y(x: int, is_odd: bool, curve: "ECCurve") -> int:
        """Decompress Y coordinate from X.

        Assumes p ≡ 3 (mod 4), which holds for both secp256r1 and
        secp256k1.  Verifies the computed square root is valid.
        """
        p = curve.p
        y_squared = (pow(x, 3, p) + curve.a * x + curve.b) % p
        y = pow(y_squared, (p + 1) // 4, p)

        # Verify the square root is correct
        if pow(y, 2, p) != y_squared:
            raise ValueError("Invalid point: x coordinate not on curve")

        if (y % 2 == 1) != is_odd:
            y = p - y
        return y
