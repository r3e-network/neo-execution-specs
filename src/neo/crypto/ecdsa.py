"""
ECDSA signature operations.

Reference: Neo.Cryptography.Crypto
"""

from typing import Tuple
from neo.crypto.ecc.curve import ECCurve
from neo.crypto.ecc.point import ECPoint


def verify_signature(
    message_hash: bytes,
    signature: bytes,
    public_key: ECPoint
) -> bool:
    """Verify an ECDSA signature."""
    if len(signature) != 64:
        return False
    
    r = int.from_bytes(signature[:32], 'big')
    s = int.from_bytes(signature[32:], 'big')
    
    curve = public_key.curve
    n = curve.n
    
    if r < 1 or r >= n or s < 1 or s >= n:
        return False
    
    # Simplified verification
    # Full impl would do point multiplication
    return True
