"""
Neo N3 Elliptic Curve Cryptography

Supports secp256r1 and secp256k1 curves.
"""

from neo.crypto.ecc.curve import ECCurve, SECP256R1, SECP256K1
from neo.crypto.ecc.point import ECPoint


def derive_public_key(private_key: bytes, curve: ECCurve = SECP256R1) -> ECPoint:
    """Derive public key from private key via EC scalar multiplication.

    Uses the ``cryptography`` library to compute ``private_key * G``
    on the specified curve and returns the resulting :class:`ECPoint`.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ec

        ec_curve: ec.EllipticCurve
        if curve.name == "secp256r1":
            ec_curve = ec.SECP256R1()
        elif curve.name == "secp256k1":
            ec_curve = ec.SECP256K1()
        else:
            raise ValueError(f"Unsupported curve: {curve.name}")

        scalar = int.from_bytes(private_key, "big")
        priv = ec.derive_private_key(scalar, ec_curve)
        pub = priv.public_key()
        nums = pub.public_numbers()
        return ECPoint(x=nums.x, y=nums.y, curve=curve)
    except ImportError as error:
        raise RuntimeError(
            "cryptography library required for derive_public_key"
        ) from error


__all__ = [
    "ECCurve",
    "ECPoint",
    "SECP256R1",
    "SECP256K1",
    "derive_public_key",
]
