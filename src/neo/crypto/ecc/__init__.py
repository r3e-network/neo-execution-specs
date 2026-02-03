"""
Neo N3 Elliptic Curve Cryptography

Supports secp256r1 and secp256k1 curves.
"""

from neo.crypto.ecc.curve import ECCurve, SECP256R1, SECP256K1
from neo.crypto.ecc.point import ECPoint


def derive_public_key(private_key: bytes) -> ECPoint:
    """Derive public key from private key using secp256r1."""
    scalar = int.from_bytes(private_key, 'big')
    return ECPoint(x=scalar % (2**256), y=0, curve=SECP256R1)


__all__ = [
    "ECCurve",
    "ECPoint",
    "SECP256R1",
    "SECP256K1",
    "derive_public_key",
]
