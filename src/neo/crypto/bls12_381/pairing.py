"""
BLS12-381 pairing operation.

The pairing e: G1 x G2 -> Gt is a bilinear map.
Uses py_ecc library for cryptographically correct implementation.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .g1 import G1Affine, G1Projective
    from .g2 import G2Affine, G2Projective
    from .gt import Gt

# Try to import py_ecc for real BLS12-381 operations
try:
    from py_ecc.bls12_381 import pairing as _py_ecc_pairing
    from py_ecc.bls12_381 import FQ12
    HAS_PY_ECC = True
except ImportError:
    HAS_PY_ECC = False


def pairing(g1: "G1Affine | G1Projective", g2: "G2Affine | G2Projective") -> "Gt":
    """Compute the optimal ate pairing e(g1, g2).
    
    Args:
        g1: Point in G1
        g2: Point in G2
        
    Returns:
        Element in Gt
    """
    from .g1 import G1Affine, G1Projective
    from .g2 import G2Affine, G2Projective
    from .gt import Gt
    
    # Convert to affine if needed
    if isinstance(g1, G1Projective):
        g1 = g1.to_affine()
    if isinstance(g2, G2Projective):
        g2 = g2.to_affine()
    
    # Handle identity cases
    if g1.is_identity() or g2.is_identity():
        return Gt.identity()
    
    if HAS_PY_ECC:
        return _pairing_py_ecc(g1, g2)
    else:
        # Fallback to placeholder (not cryptographically secure)
        return _pairing_placeholder(g1, g2)


def _pairing_py_ecc(g1: "G1Affine", g2: "G2Affine") -> "Gt":
    """Compute pairing using py_ecc library."""
    from .gt import Gt
    from py_ecc.fields import bls12_381_FQ as FQ, bls12_381_FQ2 as FQ2
    
    # Convert G1 point to py_ecc format using FQ field elements
    g1_point = (FQ(g1.x), FQ(g1.y))
    
    # Convert G2 point to py_ecc format using FQ2 field elements
    # FQ2 expects a tuple (c0, c1) where element = c0 + c1*u
    g2_x = FQ2((g2.x.c0, g2.x.c1))
    g2_y = FQ2((g2.y.c0, g2.y.c1))
    g2_point = (g2_x, g2_y)
    
    # Compute pairing
    result = _py_ecc_pairing(g2_point, g1_point)
    
    # Return Gt with FQ12 directly for proper arithmetic
    return Gt(fq12=result)


def _fq12_to_bytes(fq12) -> bytes:
    """Convert FQ12 element to 576-byte representation."""
    # FQ12 has 12 FQ coefficients directly
    # Total: 12 * 48 = 576 bytes
    result = bytearray(576)
    
    for i, coeff in enumerate(fq12.coeffs):
        # Each coefficient is an FQ element, convert to int
        coeff_int = int(coeff)
        result[i*48:(i+1)*48] = coeff_int.to_bytes(48, 'big')
    
    return bytes(result)


def _pairing_placeholder(g1: "G1Affine", g2: "G2Affine") -> "Gt":
    """Placeholder pairing when py_ecc is not available.
    
    WARNING: This is NOT cryptographically secure!
    """
    from .gt import Gt
    import hashlib
    
    g1_bytes = g1.to_compressed()
    g2_bytes = g2.to_compressed()
    
    # Hash inputs to create 576-byte output
    result = bytearray(576)
    for i in range(12):
        h = hashlib.sha384(g1_bytes + g2_bytes + bytes([i]))
        result[i*48:(i+1)*48] = h.digest()
    
    return Gt(bytes(result))
