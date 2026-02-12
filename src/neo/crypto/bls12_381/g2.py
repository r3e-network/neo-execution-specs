"""
BLS12-381 G2 group elements.

G2 is the group of points on the twisted curve over Fp2.
Points are represented in compressed form as 96 bytes.
"""

from __future__ import annotations

from .scalar import Scalar, SCALAR_MODULUS


# BLS12-381 base field modulus
P = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab


class Fp2:
    """Element of Fp2 = Fp[u]/(u^2 + 1)."""
    
    __slots__ = ('c0', 'c1')
    
    def __init__(self, c0: int = 0, c1: int = 0) -> None:
        self.c0 = c0 % P
        self.c1 = c1 % P
    
    @classmethod
    def zero(cls) -> Fp2:
        return cls(0, 0)
    
    @classmethod
    def one(cls) -> Fp2:
        return cls(1, 0)
    
    def is_zero(self) -> bool:
        return self.c0 == 0 and self.c1 == 0
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Fp2):
            return self.c0 == other.c0 and self.c1 == other.c1
        return False
    
    def __neg__(self) -> Fp2:
        return Fp2(P - self.c0 if self.c0 else 0, 
                   P - self.c1 if self.c1 else 0)
    
    def __add__(self, other: Fp2) -> Fp2:
        return Fp2((self.c0 + other.c0) % P, 
                   (self.c1 + other.c1) % P)
    
    def __sub__(self, other: Fp2) -> Fp2:
        return Fp2((self.c0 - other.c0) % P, 
                   (self.c1 - other.c1) % P)
    
    def __mul__(self, other: Fp2) -> Fp2:
        # (a + bu)(c + du) = (ac - bd) + (ad + bc)u
        ac = (self.c0 * other.c0) % P
        bd = (self.c1 * other.c1) % P
        ad = (self.c0 * other.c1) % P
        bc = (self.c1 * other.c0) % P
        return Fp2((ac - bd) % P, (ad + bc) % P)
    
    def square(self) -> Fp2:
        return self * self
    
    def invert(self) -> Fp2:
        # 1/(a + bu) = (a - bu)/(a^2 + b^2)
        denom = (self.c0 * self.c0 + self.c1 * self.c1) % P
        denom_inv = pow(denom, -1, P)
        return Fp2((self.c0 * denom_inv) % P, 
                   (P - self.c1 * denom_inv) % P)


# G2 curve coefficient b' = 4(1 + u)
B_G2 = Fp2(4, 4)


class G2Affine:
    """G2 point in affine coordinates over Fp2."""
    
    __slots__ = ('x', 'y', '_is_infinity')
    
    def __init__(self, x: Fp2 | None = None, y: Fp2 | None = None, is_infinity: bool = False) -> None:
        self.x = x if x else Fp2.zero()
        self.y = y if y else Fp2.zero()
        self._is_infinity = is_infinity
    
    @classmethod
    def identity(cls) -> G2Affine:
        return cls(is_infinity=True)
    
    @classmethod
    def generator(cls) -> G2Affine:
        """Return the generator point for G2."""
        # BLS12-381 G2 generator coordinates
        x_c0 = 0x024aa2b2f08f0a91260805272dc51051c6e47ad4fa403b02b4510b647ae3d1770bac0326a805bbefd48056c8c121bdb8
        x_c1 = 0x13e02b6052719f607dacd3a088274f65596bd0d09920b61ab5da61bbdc7f5049334cf11213945d57e5ac7d055d042b7e
        y_c0 = 0x0ce5d527727d6e118cc9cdc6da2e351aadfd9baa8cbdd3a76d429a695160d12c923ac9cc3baca289e193548608b82801
        y_c1 = 0x0606c4a02ea734cc32acd2b02bc28b99cb3e287e85a763af267492ab572e99ab3f370d275cec1da1aaa9075ff05f79be
        return cls(Fp2(x_c0, x_c1), Fp2(y_c0, y_c1))
    
    @classmethod
    def from_compressed(cls, data: bytes) -> G2Affine:
        """Deserialize from 96-byte compressed format."""
        if len(data) != 96:
            raise ValueError("G2 compressed point must be 96 bytes")
        
        flags = data[0] & 0xe0
        is_infinity = (flags & 0x40) != 0
        is_y_odd = (flags & 0x20) != 0
        
        if is_infinity:
            return cls.identity()
        
        # Extract x coordinate (two Fp elements)
        x_c1_bytes = bytes([data[0] & 0x1f]) + data[1:48]
        x_c0_bytes = data[48:96]
        
        x_c1 = int.from_bytes(x_c1_bytes, 'big')
        x_c0 = int.from_bytes(x_c0_bytes, 'big')
        x = Fp2(x_c0, x_c1)
        
        # Compute y from curve equation
        y_squared = x * x * x + B_G2
        y = _fp2_sqrt(y_squared)
        
        if y is None:
            raise ValueError("Invalid point: not on curve")
        
        # Choose correct y based on lexicographic ordering
        if _fp2_is_odd(y) != is_y_odd:
            y = -y
        
        return cls(x, y)
    
    def to_compressed(self) -> bytes:
        """Serialize to 96-byte compressed format."""
        if self._is_infinity:
            result = bytearray(96)
            result[0] = 0xc0
            return bytes(result)
        
        c1_bytes = self.x.c1.to_bytes(48, 'big')
        c0_bytes = self.x.c0.to_bytes(48, 'big')
        
        result = bytearray(c1_bytes + c0_bytes)
        result[0] |= 0x80  # compressed flag
        
        if _fp2_is_odd(self.y):
            result[0] |= 0x20
        
        return bytes(result)
    
    def is_identity(self) -> bool:
        return self._is_infinity
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, G2Affine):
            if self._is_infinity and other._is_infinity:
                return True
            if self._is_infinity or other._is_infinity:
                return False
            return self.x == other.x and self.y == other.y
        return False
    
    def __neg__(self) -> G2Affine:
        if self._is_infinity:
            return G2Affine.identity()
        return G2Affine(self.x, -self.y)
    
    def __add__(self, other: G2Affine | G2Projective) -> G2Projective:
        return G2Projective.from_affine(self) + other
    
    def __mul__(self, scalar: int | Scalar) -> G2Projective:
        return G2Projective.from_affine(self) * scalar


def _fp2_is_odd(x: Fp2) -> bool:
    """Lexicographic oddness for Fp2."""
    if x.c1 != 0:
        return x.c1 & 1 == 1
    return x.c0 & 1 == 1


def _fp_sqrt(a: int) -> int | None:
    """Square root in Fp. For p ≡ 3 (mod 4), sqrt(a) = a^((p+1)/4)."""
    if a == 0:
        return 0
    if pow(a, (P - 1) // 2, P) != 1:
        return None  # Not a quadratic residue
    return pow(a, (P + 1) // 4, P)


def _fp2_sqrt(x: Fp2) -> Fp2 | None:
    """Square root in Fp2 = Fp[u]/(u^2 + 1).

    Uses the algorithm: for a = a0 + a1·u,
    1. Compute norm t = sqrt(a0² + a1²) in Fp
    2. Compute x0 = sqrt((a0 + t) / 2) in Fp
    3. x1 = a1 / (2·x0)
    4. Return x0 + x1·u
    """
    if x.is_zero():
        return Fp2.zero()

    a0, a1 = x.c0, x.c1

    # Special case: purely real
    if a1 == 0:
        s = _fp_sqrt(a0)
        if s is not None:
            return Fp2(s, 0)
        # a0 is not a QR, so -a0 must be; return sqrt(-a0)·u
        s = _fp_sqrt((P - a0) % P)
        if s is None:
            return None
        return Fp2(0, s)

    # General case
    # norm = a0² + a1² (the field norm N(a) for Fp2 with u²=-1)
    norm = (a0 * a0 + a1 * a1) % P
    t = _fp_sqrt(norm)
    if t is None:
        return None

    # inv2 = modular inverse of 2
    inv2 = (P + 1) // 2

    # Try x0 = sqrt((a0 + t) / 2)
    half = ((a0 + t) * inv2) % P
    x0 = _fp_sqrt(half)
    if x0 is None:
        # Use -t instead
        half = ((a0 - t + P) * inv2) % P
        x0 = _fp_sqrt(half)
        if x0 is None:
            return None

    # x1 = a1 / (2·x0)
    x1 = (a1 * pow(2 * x0, -1, P)) % P

    result = Fp2(x0, x1)
    # Verify
    if result * result == x:
        return result
    return None


class G2Projective:
    """G2 point in projective coordinates over Fp2."""
    
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x: Fp2 | None = None, y: Fp2 | None = None, z: Fp2 | None = None) -> None:
        self.x = x if x else Fp2.zero()
        self.y = y if y else Fp2.one()
        self.z = z if z else Fp2.zero()
    
    @classmethod
    def identity(cls) -> G2Projective:
        return cls(Fp2.zero(), Fp2.one(), Fp2.zero())
    
    @classmethod
    def from_affine(cls, p: G2Affine) -> G2Projective:
        if p._is_infinity:
            return cls.identity()
        return cls(p.x, p.y, Fp2.one())
    
    def to_affine(self) -> G2Affine:
        if self.z.is_zero():
            return G2Affine.identity()
        # Jacobian coordinates: (x, y) = (X/Z^2, Y/Z^3)
        z_inv = self.z.invert()
        z_inv2 = z_inv * z_inv
        z_inv3 = z_inv2 * z_inv
        return G2Affine(self.x * z_inv2, self.y * z_inv3)
    
    def to_compressed(self) -> bytes:
        return self.to_affine().to_compressed()
    
    def is_identity(self) -> bool:
        return self.z.is_zero()
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, G2Projective):
            if self.z.is_zero() and other.z.is_zero():
                return True
            if self.z.is_zero() or other.z.is_zero():
                return False
            # Jacobian: affine x = X/Z², y = Y/Z³
            z1_sq = self.z * self.z
            z2_sq = other.z * other.z
            z1_cu = z1_sq * self.z
            z2_cu = z2_sq * other.z
            return (self.x * z2_sq) == (other.x * z1_sq) and \
                   (self.y * z2_cu) == (other.y * z1_cu)
        return False
    
    def __neg__(self) -> G2Projective:
        return G2Projective(self.x, -self.y, self.z)
    
    def __add__(self, other: G2Affine | G2Projective) -> G2Projective:
        if isinstance(other, G2Affine):
            other = G2Projective.from_affine(other)
        return self._add_projective(other)
    
    def _add_projective(self, other: G2Projective) -> G2Projective:
        if self.z.is_zero():
            return other
        if other.z.is_zero():
            return self
        
        # Jacobian addition formula
        z1_sq = self.z * self.z
        z2_sq = other.z * other.z
        z1_cu = z1_sq * self.z
        z2_cu = z2_sq * other.z
        
        u1 = self.x * z2_sq
        u2 = other.x * z1_sq
        s1 = self.y * z2_cu
        s2 = other.y * z1_cu
        
        if u1 == u2:
            if s1 == s2:
                return self._double()
            return G2Projective.identity()
        
        h = u2 - u1
        r = s2 - s1
        h2 = h * h
        h3 = h2 * h
        
        x3 = r * r - h3 - (u1 * h2) - (u1 * h2)
        y3 = r * (u1 * h2 - x3) - s1 * h3
        z3 = h * self.z * other.z
        
        return G2Projective(x3, y3, z3)
    
    def _double(self) -> G2Projective:
        if self.z.is_zero():
            return self
        
        a = self.x * self.x
        b = self.y * self.y
        c = b * b
        
        d = (self.x + b) * (self.x + b) - a - c
        d = d + d
        e = a + a + a
        f = e * e
        
        x3 = f - d - d
        y3 = e * (d - x3) - (c + c + c + c + c + c + c + c)
        z3 = (self.y * self.z) + (self.y * self.z)
        
        return G2Projective(x3, y3, z3)
    
    def __mul__(self, scalar: int | Scalar) -> G2Projective:
        if isinstance(scalar, Scalar):
            scalar = scalar.value
        scalar = scalar % SCALAR_MODULUS
        
        result = G2Projective.identity()
        temp = self
        
        while scalar > 0:
            if scalar & 1:
                result = result + temp
            temp = temp._double()
            scalar >>= 1
        
        return result
    
    def __rmul__(self, scalar: int | Scalar) -> G2Projective:
        return self * scalar
