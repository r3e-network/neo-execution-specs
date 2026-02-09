"""
ECDSA signature operations.

Reference: Neo.Cryptography.Crypto
"""

from neo.crypto.ecc.point import ECPoint
from neo.crypto.ecc.signature import verify_signature as _verify_sig


def verify_signature(
    message_hash: bytes,
    signature: bytes,
    public_key: ECPoint
) -> bool:
    """Verify an ECDSA signature.
    
    Args:
        message_hash: The hash of the message that was signed.
        signature: The signature (64 bytes: r || s).
        public_key: The public key as ECPoint.
        
    Returns:
        True if the signature is valid, False otherwise.
    """
    if len(signature) != 64:
        return False
    
    # Encode public key to bytes
    pubkey_bytes = public_key.encode(compressed=True)
    
    # Use the full implementation from signature module
    return _verify_sig(message_hash, signature, pubkey_bytes, public_key.curve)
