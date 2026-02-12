"""
BLS12-381 Gt group element.

Gt is the target group of the pairing, a subgroup of Fp12*.
Elements are represented as 576 bytes.
Uses py_ecc library for cryptographically correct implementation.
"""

from __future__ import annotations

from typing import Any

from .scalar import Scalar, SCALAR_MODULUS


# BLS12-381 base field modulus
P = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab

# Try to import py_ecc for real Fp12 operations
try:
    from py_ecc.fields import bls12_381_FQ12 as FQ12
    HAS_PY_ECC = True
except ImportError:
    HAS_PY_ECC = False


class Gt:
    """Element of the target group Gt (subgroup of Fp12*).
    
    When py_ecc is available, uses proper Fp12 arithmetic.
    Otherwise falls back to byte representation with placeholder operations.
    """
    
    __slots__ = ('_data', '_fq12')
    _data: bytes
    _fq12: Any | None
    
    def __init__(self, data: bytes | None = None, fq12: Any | None = None) -> None:
        """Initialize Gt element."""
        self._fq12 = fq12
        
        if data is None and fq12 is None:
            # Identity element
            self._data = self._identity_bytes()
            if HAS_PY_ECC:
                self._fq12 = FQ12.one()
        elif fq12 is not None:
            # Initialize from FQ12
            self._fq12 = fq12
            self._data = self._fq12_to_bytes(fq12)
        else:
            assert data is not None
            if len(data) != 576:
                raise ValueError("Gt element must be 576 bytes")
            self._data = bytes(data)
            if HAS_PY_ECC:
                self._fq12 = self._bytes_to_fq12(data)
    
    @classmethod
    def identity(cls) -> Gt:
        """Return the identity element (1 in multiplicative notation)."""
        return cls()
    
    @staticmethod
    def _identity_bytes() -> bytes:
        """Return bytes for identity element."""
        # Identity in Fp12 is 1 (first coefficient = 1, rest = 0)
        result = bytearray(576)
        result[47] = 1
        return bytes(result)
    
    @staticmethod
    def _fq12_to_bytes(fq12) -> bytes:
        """Convert FQ12 element to 576-byte representation."""
        result = bytearray(576)
        for i, coeff in enumerate(fq12.coeffs):
            coeff_int = int(coeff)
            result[i*48:(i+1)*48] = coeff_int.to_bytes(48, 'big')
        return bytes(result)
    
    @staticmethod
    def _bytes_to_fq12(data: bytes):
        """Convert 576-byte representation to FQ12 element."""
        if not HAS_PY_ECC:
            return None
        coeffs = []
        for i in range(12):
            coeff = int.from_bytes(data[i*48:(i+1)*48], 'big')
            coeffs.append(coeff)
        return FQ12(coeffs)
    
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
        if HAS_PY_ECC and self._fq12 is not None:
            return self._fq12 == FQ12.one()
        return self._data == self._identity_bytes()
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Gt):
            if HAS_PY_ECC and self._fq12 is not None and other._fq12 is not None:
                return self._fq12 == other._fq12
            return self._data == other._data
        return False
    
    def __hash__(self) -> int:
        return hash(self._data)
    
    def __mul__(self, other: Gt) -> Gt:
        """Multiply two Gt elements (group operation in Fp12*)."""
        if HAS_PY_ECC and self._fq12 is not None and other._fq12 is not None:
            result_fq12 = self._fq12 * other._fq12
            return Gt(fq12=result_fq12)
        # Fallback: XOR (not cryptographically correct)
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
            return Gt(fq12=self._fq12) if self._fq12 else Gt(self._data)
        
        # Square-and-multiply
        result = Gt.identity()
        temp = Gt(fq12=self._fq12) if self._fq12 else Gt(self._data)
        
        while scalar > 0:
            if scalar & 1:
                result = result * temp
            temp = temp * temp
            scalar >>= 1
        
        return result
    
    def __repr__(self) -> str:
        return f"Gt({self._data[:8].hex()}...)"
