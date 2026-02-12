"""
Ed25519 signature operations.

Reference: Neo.Cryptography.Ed25519
"""

# Try to import cryptography library
INVALID_SIGNATURE_ERROR: type[Exception] = Exception

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.exceptions import InvalidSignature as _InvalidSignature

    HAS_ED25519 = True
    INVALID_SIGNATURE_ERROR = _InvalidSignature
except ImportError:
    HAS_ED25519 = False
    INVALID_SIGNATURE_ERROR = Exception


def ed25519_verify(
    message: bytes,
    signature: bytes,
    pubkey: bytes,
) -> bool:
    """Verify an Ed25519 signature."""
    if len(pubkey) != 32:
        return False
    if len(signature) != 64:
        return False

    if not HAS_ED25519:
        return False

    try:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pubkey)
        public_key.verify(signature, message)
        return True
    except (INVALID_SIGNATURE_ERROR, ValueError):
        return False
