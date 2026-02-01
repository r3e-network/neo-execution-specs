"""
Neo address utilities.

Reference: Neo.Wallets.Helper
"""

from neo.crypto.base58 import base58_check_encode, base58_check_decode
from neo.crypto.hash import hash160


def script_hash_to_address(script_hash: bytes, version: int = 53) -> str:
    """Convert script hash to Neo address."""
    return base58_check_encode(bytes([version]) + script_hash)


def address_to_script_hash(address: str) -> bytes:
    """Convert Neo address to script hash."""
    data = base58_check_decode(address)
    return data[1:]  # Remove version byte
