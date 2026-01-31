"""Hash functions."""

import hashlib


def sha256(data: bytes) -> bytes:
    """SHA-256 hash."""
    return hashlib.sha256(data).digest()


def ripemd160(data: bytes) -> bytes:
    """RIPEMD-160 hash."""
    h = hashlib.new('ripemd160')
    h.update(data)
    return h.digest()


def hash256(data: bytes) -> bytes:
    """Double SHA-256."""
    return sha256(sha256(data))


def hash160(data: bytes) -> bytes:
    """SHA-256 then RIPEMD-160."""
    return ripemd160(sha256(data))
