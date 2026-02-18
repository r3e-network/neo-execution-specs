"""Neo N3 Key Pair implementation."""

import secrets
from dataclasses import dataclass

from neo.crypto.ecc import ECPoint, derive_public_key
from neo.crypto.ecdsa import verify_signature as verify_ecdsa_signature
from neo.crypto.hash import hash256

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, utils

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


@dataclass(frozen=True)
class KeyPair:
    """Represents a public/private key pair."""

    private_key: bytes
    public_key: ECPoint

    def __post_init__(self):
        if len(self.private_key) != 32:
            raise ValueError("Private key must be 32 bytes")

    @classmethod
    def generate(cls) -> "KeyPair":
        """Generate a new random key pair."""
        private_key = secrets.token_bytes(32)
        return cls.from_private_key(private_key)

    @classmethod
    def from_private_key(cls, private_key: bytes) -> "KeyPair":
        """Create key pair from private key."""
        if len(private_key) != 32:
            raise ValueError("Private key must be 32 bytes")

        public_key = derive_public_key(private_key)
        return cls(private_key=private_key, public_key=public_key)

    @classmethod
    def from_wif(cls, wif: str) -> "KeyPair":
        """Import key pair from WIF format."""
        decoded = base58_check_decode(wif)

        if len(decoded) == 34 and decoded[0] == 0x80 and decoded[-1] == 0x01:
            private_key = decoded[1:33]
        elif len(decoded) == 33 and decoded[0] == 0x80:
            private_key = decoded[1:33]
        else:
            raise ValueError("Invalid WIF format")

        return cls.from_private_key(private_key)

    def to_wif(self) -> str:
        """Export private key to WIF format."""
        data = bytes([0x80]) + self.private_key + bytes([0x01])
        return base58_check_encode(data)

    def sign(self, message: bytes) -> bytes:
        """Sign a message with ECDSA/secp256r1 and return r||s bytes."""
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("cryptography library required for signing")

        message_hash = hash256(message)
        scalar = int.from_bytes(self.private_key, "big")
        private = ec.derive_private_key(scalar, ec.SECP256R1())
        der_signature = private.sign(
            message_hash,
            ec.ECDSA(utils.Prehashed(hashes.SHA256())),
        )
        r, s = utils.decode_dss_signature(der_signature)
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")

    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify an ECDSA signature."""
        return verify_ecdsa_signature(hash256(message), signature, self.public_key)


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58_encode(data: bytes) -> str:
    """Encode bytes to base58."""
    num = int.from_bytes(data, 'big')
    result = ""

    while num > 0:
        num, remainder = divmod(num, 58)
        result = BASE58_ALPHABET[remainder] + result

    for byte in data:
        if byte == 0:
            result = "1" + result
        else:
            break

    return result or "1"


def base58_decode(s: str) -> bytes:
    """Decode base58 to bytes."""
    num = 0
    for char in s:
        num = num * 58 + BASE58_ALPHABET.index(char)

    result: list[int] = []
    while num > 0:
        num, remainder = divmod(num, 256)
        result.append(remainder)
    result.reverse()

    leading_ones = 0
    for char in s:
        if char == '1':
            leading_ones += 1
        else:
            break

    return bytes([0] * leading_ones + result)


def base58_check_encode(data: bytes) -> str:
    """Encode with checksum."""
    checksum = hash256(data)[:4]
    return base58_encode(data + checksum)


def base58_check_decode(s: str) -> bytes:
    """Decode and verify checksum."""
    data = base58_decode(s)
    payload, checksum = data[:-4], data[-4:]

    if hash256(payload)[:4] != checksum:
        raise ValueError("Invalid checksum")

    return payload
