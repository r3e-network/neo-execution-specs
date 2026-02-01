"""
BLS12-381 elliptic curve operations.

Reference: Neo.Cryptography.BLS12_381

This module provides BLS12-381 curve operations for:
- G1 group (48-byte compressed points)
- G2 group (96-byte compressed points)  
- Gt group (576-byte elements)
- Pairing operations
"""

from .g1 import G1Affine, G1Projective
from .g2 import G2Affine, G2Projective
from .gt import Gt
from .scalar import Scalar
from .pairing import pairing

__all__ = [
    "G1Affine",
    "G1Projective", 
    "G2Affine",
    "G2Projective",
    "Gt",
    "Scalar",
    "pairing",
]
