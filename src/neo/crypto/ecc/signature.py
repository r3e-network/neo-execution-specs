"""
ECDSA Signature verification.

Reference: Neo.Cryptography.Crypto
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.crypto.ecc.curve import ECCurve

# Try to import cryptography library
try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    InvalidSignature = Exception  # Fallback


def verify_signature(
    message: bytes,
    signature: bytes,
    pubkey: bytes,
    curve: "ECCurve"
) -> bool:
    """Verify an ECDSA signature.
    
    Args:
        message: The message that was signed.
        signature: The signature (64 bytes: r || s).
        pubkey: The public key (33 or 65 bytes).
        curve: The elliptic curve to use.
        
    Returns:
        True if the signature is valid, False otherwise.
    """
    # Validate input lengths first
    if len(pubkey) not in (33, 65):
        return False
    if len(signature) != 64:
        return False
    
    if not HAS_CRYPTOGRAPHY:
        # Fallback: return False when library not available
        return False
    
    try:
        # Parse public key
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            _get_curve_instance(curve), pubkey
        )
        
        # Parse signature (r || s, each 32 bytes)
        r = int.from_bytes(signature[:32], 'big')
        s = int.from_bytes(signature[32:], 'big')
        
        # Convert to DER format for cryptography library
        der_sig = _encode_der_signature(r, s)
        
        # Verify
        public_key.verify(der_sig, message, ec.ECDSA(hashes.SHA256()))
        return True
        
    except (InvalidSignature, ValueError, Exception):
        return False


def _get_curve_instance(curve: "ECCurve"):
    """Get cryptography library curve instance."""
    if curve.name == "secp256r1":
        return ec.SECP256R1()
    elif curve.name == "secp256k1":
        return ec.SECP256K1()
    else:
        raise ValueError(f"Unsupported curve: {curve.name}")


def _encode_der_signature(r: int, s: int) -> bytes:
    """Encode r, s as DER signature."""
    def encode_int(val: int) -> bytes:
        length = (val.bit_length() + 8) // 8
        b = val.to_bytes(length, 'big')
        if b[0] & 0x80:
            b = b'\x00' + b
        return b'\x02' + bytes([len(b)]) + b
    
    r_enc = encode_int(r)
    s_enc = encode_int(s)
    content = r_enc + s_enc
    return b'\x30' + bytes([len(content)]) + content
