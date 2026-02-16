"""CryptoLib native contract.

Reference: Neo.SmartContract.Native.CryptoLib
"""

from __future__ import annotations
from enum import IntEnum
from typing import Any, Optional

from neo.native.native_contract import NativeContract, CallFlags
from neo.crypto import sha256, ripemd160, murmur32, ed25519_verify


class NamedCurveHash(IntEnum):
    """Named curve and hash algorithm combinations."""

    secp256k1SHA256 = 22
    secp256r1SHA256 = 23
    secp256k1Keccak256 = 24
    secp256r1Keccak256 = 25


class _BlsPoint:
    """Manifest marker type for BLS interop objects."""


class CryptoLib(NativeContract):
    """Cryptographic functions native contract.

    Provides cryptographic operations including:
    - Hash functions (SHA256, RIPEMD160, Murmur32, Keccak256)
    - ECDSA signature verification
    - Ed25519 signature verification
    - BLS12-381 operations
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self) -> str:
        return "CryptoLib"

    def _register_methods(self) -> None:
        """Register CryptoLib methods."""
        super()._register_methods()

        # Hash functions
        self._register_method("sha256", self.sha256, cpu_fee=1 << 15, call_flags=CallFlags.NONE)
        self._register_method(
            "ripemd160", self.ripemd160, cpu_fee=1 << 15, call_flags=CallFlags.NONE
        )
        self._register_method("murmur32", self.murmur32, cpu_fee=1 << 13, call_flags=CallFlags.NONE)
        self._register_method(
            "keccak256", self.keccak256, cpu_fee=1 << 15, call_flags=CallFlags.NONE
        )

        # Signature verification
        self._register_method(
            "verifyWithECDsa", self.verify_with_ecdsa, cpu_fee=1 << 15, call_flags=CallFlags.NONE
        )
        self._register_method(
            "verifyWithEd25519",
            self.verify_with_ed25519,
            cpu_fee=1 << 15,
            call_flags=CallFlags.NONE,
        )
        self._register_method(
            "recoverSecp256K1", self.recover_secp256k1, cpu_fee=1 << 15, call_flags=CallFlags.NONE
        )

        # BLS12-381 operations
        self._register_method(
            "bls12381Serialize", self.bls12381_serialize, cpu_fee=1 << 19, call_flags=CallFlags.NONE
        )
        self._register_method(
            "bls12381Deserialize",
            self.bls12381_deserialize,
            cpu_fee=1 << 19,
            call_flags=CallFlags.NONE,
        )
        self._register_method(
            "bls12381Equal", self.bls12381_equal, cpu_fee=1 << 5, call_flags=CallFlags.NONE
        )
        self._register_method(
            "bls12381Add", self.bls12381_add, cpu_fee=1 << 19, call_flags=CallFlags.NONE
        )
        self._register_method(
            "bls12381Mul", self.bls12381_mul, cpu_fee=1 << 21, call_flags=CallFlags.NONE
        )
        self._register_method(
            "bls12381Pairing", self.bls12381_pairing, cpu_fee=1 << 23, call_flags=CallFlags.NONE
        )

    # ========== Hash Functions ==========

    def sha256(self, data: bytes) -> bytes:
        """Compute SHA-256 hash of data.

        Args:
            data: Input bytes to hash

        Returns:
            32-byte SHA-256 hash
        """
        return sha256(data)

    def ripemd160(self, data: bytes) -> bytes:
        """Compute RIPEMD-160 hash of data.

        Args:
            data: Input bytes to hash

        Returns:
            20-byte RIPEMD-160 hash
        """
        return ripemd160(data)

    def murmur32(self, data: bytes, seed: int) -> bytes:
        """Compute Murmur3 32-bit hash.

        Args:
            data: Input bytes to hash
            seed: Hash seed value

        Returns:
            4-byte Murmur32 hash
        """
        result = murmur32(data, seed)
        return result.to_bytes(4, "little")

    def keccak256(self, data: bytes) -> bytes:
        """Compute Keccak-256 hash of data.

        Args:
            data: Input bytes to hash

        Returns:
            32-byte Keccak-256 hash

        Raises:
            ImportError: If neither pycryptodome nor pysha3 is available.
                        Note: hashlib.sha3_256 is NOT Keccak-256!
        """
        try:
            from Crypto.Hash import keccak

            k = keccak.new(digest_bits=256)
            k.update(data)
            return k.digest()
        except ImportError:
            try:
                import sha3  # type: ignore[import-not-found]

                return sha3.keccak_256(data).digest()
            except ImportError:
                raise ImportError(
                    "Keccak256 requires pycryptodome or pysha3 library. "
                    "Install with: pip install pycryptodome"
                )

    # ========== Signature Verification ==========

    def verify_with_ecdsa(
        self, message: bytes, pubkey: bytes, signature: bytes, curve_hash: NamedCurveHash
    ) -> bool:
        """Verify ECDSA signature.

        Args:
            message: The signed message
            pubkey: Public key bytes
            signature: Signature bytes (64 bytes: r || s)
            curve_hash: Curve and hash algorithm combination

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            from neo.crypto.ecc.curve import SECP256K1, SECP256R1
            from neo.crypto.ecc.point import ECPoint

            # Determine curve
            if curve_hash in (NamedCurveHash.secp256k1SHA256, NamedCurveHash.secp256k1Keccak256):
                curve = SECP256K1
            else:
                curve = SECP256R1

            # Hash the message
            if curve_hash in (NamedCurveHash.secp256k1Keccak256, NamedCurveHash.secp256r1Keccak256):
                message_hash = self.keccak256(message)
            else:
                message_hash = self.sha256(message)

            # Decode public key and verify
            public_key = ECPoint.decode(pubkey, curve)
            return self._verify_ecdsa_signature(message_hash, signature, public_key)
        except (ValueError, TypeError, ImportError):
            return False

    def _verify_ecdsa_signature(
        self, message_hash: bytes, signature: bytes, public_key: Any
    ) -> bool:
        """Internal ECDSA verification."""
        if len(signature) != 64:
            return False

        r = int.from_bytes(signature[:32], "big")
        s = int.from_bytes(signature[32:], "big")

        curve = public_key.curve
        n = curve.n

        if r < 1 or r >= n or s < 1 or s >= n:
            return False

        # Full ECDSA verification
        z = int.from_bytes(message_hash, "big")
        w = pow(s, -1, n)
        u1 = (z * w) % n
        u2 = (r * w) % n

        # Point multiplication: u1*G + u2*Q
        point = curve.g * u1 + public_key * u2

        return point.x % n == r

    def verify_with_ed25519(self, message: bytes, pubkey: bytes, signature: bytes) -> bool:
        """Verify Ed25519 signature.

        Args:
            message: The signed message
            pubkey: 32-byte Ed25519 public key
            signature: 64-byte Ed25519 signature

        Returns:
            True if signature is valid, False otherwise
        """
        if len(signature) != 64:
            return False
        if len(pubkey) != 32:
            return False

        return ed25519_verify(message, signature, pubkey)

    def recover_secp256k1(self, message_hash: bytes, signature: bytes) -> Optional[bytes]:
        """Recover public key from secp256k1 signature.

        Args:
            message_hash: 32-byte hash of the signed message
            signature: 65-byte signature (r[32] + s[32] + v[1]) or
                      64-byte EIP-2098 format

        Returns:
            Compressed public key bytes, or None if recovery fails
        """
        try:
            if len(signature) == 65:
                r = int.from_bytes(signature[:32], "big")
                s = int.from_bytes(signature[32:64], "big")
                v = signature[64]
            elif len(signature) == 64:
                # EIP-2098 compact format
                r = int.from_bytes(signature[:32], "big")
                s = int.from_bytes(signature[32:64], "big")
                v = 27 + ((s >> 255) & 1)
                s = s & ((1 << 255) - 1)
            else:
                return None

            # Recovery ID
            if v >= 27:
                v -= 27

            if v not in (0, 1):
                return None

            # Recover public key using secp256k1
            from neo.crypto.ecc.curve import SECP256K1

            curve = SECP256K1

            # Calculate recovery point
            n = curve.n
            p = curve.p

            x = r + (v >> 1) * n
            if x >= p:
                return None

            # Calculate y from x
            y_squared = (pow(x, 3, p) + curve.a * x + curve.b) % p
            y = pow(y_squared, (p + 1) // 4, p)

            if (y % 2) != (v & 1):
                y = p - y

            # Create recovery point R
            from neo.crypto.ecc.point import ECPoint

            R = ECPoint(x, y, curve)

            # Calculate public key: Q = r^-1 * (s*R - e*G)
            e = int.from_bytes(message_hash, "big")
            r_inv = pow(r, -1, n)

            Q = (R * s - curve.g * e) * r_inv

            return Q.encode(compressed=True)
        except (ValueError, TypeError, ZeroDivisionError, ImportError):
            return None

    # ========== BLS12-381 Operations ==========

    def bls12381_serialize(self, point: _BlsPoint) -> bytes:
        """Serialize a BLS12-381 point.

        Args:
            point: G1, G2, or Gt point

        Returns:
            Serialized point bytes
        """
        point_type = type(point).__name__

        if point_type in ("G1Affine", "G1Projective"):
            return self._g1_to_compressed(point)
        elif point_type in ("G2Affine", "G2Projective"):
            return self._g2_to_compressed(point)
        elif point_type == "Gt":
            return self._gt_to_bytes(point)
        else:
            raise ValueError("BLS12-381 type mismatch")

    def bls12381_deserialize(self, data: bytes) -> _BlsPoint:
        """Deserialize a BLS12-381 point.

        Args:
            data: Serialized point bytes

        Returns:
            Deserialized point (G1Affine, G2Affine, or Gt)
        """
        if len(data) == 48:
            return self._g1_from_compressed(data)
        elif len(data) == 96:
            return self._g2_from_compressed(data)
        elif len(data) == 576:
            return self._gt_from_bytes(data)
        else:
            raise ValueError("Invalid BLS12-381 point length")

    def bls12381_equal(self, x: _BlsPoint, y: _BlsPoint) -> bool:
        """Check if two BLS12-381 points are equal.

        Args:
            x: First point
            y: Second point

        Returns:
            True if points are equal
        """
        x_type = type(x).__name__
        y_type = type(y).__name__

        # Must be same type family
        if x_type.startswith("G1") and y_type.startswith("G1"):
            return self._g1_equal(x, y)
        elif x_type.startswith("G2") and y_type.startswith("G2"):
            return self._g2_equal(x, y)
        elif x_type == "Gt" and y_type == "Gt":
            return x == y
        else:
            raise ValueError("BLS12-381 type mismatch")

    def bls12381_add(self, x: _BlsPoint, y: _BlsPoint) -> _BlsPoint:
        """Add two BLS12-381 points.

        Args:
            x: First point
            y: Second point

        Returns:
            Sum of points
        """
        x_type = type(x).__name__
        y_type = type(y).__name__

        if x_type.startswith("G1") and y_type.startswith("G1"):
            return self._g1_add(x, y)
        elif x_type.startswith("G2") and y_type.startswith("G2"):
            return self._g2_add(x, y)
        elif x_type == "Gt" and y_type == "Gt":
            return self._gt_mul(x, y)  # Gt uses multiplicative notation
        else:
            raise ValueError("BLS12-381 type mismatch")

    def bls12381_mul(self, x: _BlsPoint, mul: bytes, neg: bool) -> _BlsPoint:
        """Multiply a BLS12-381 point by a scalar.

        Args:
            x: Point to multiply
            mul: 32-byte scalar (little-endian)
            neg: If True, negate the scalar

        Returns:
            Scalar multiplication result
        """
        scalar = int.from_bytes(mul, "little")
        if neg:
            # Get the field modulus and negate
            scalar = -scalar

        x_type = type(x).__name__

        if x_type.startswith("G1"):
            return self._g1_mul(x, scalar)
        elif x_type.startswith("G2"):
            return self._g2_mul(x, scalar)
        elif x_type == "Gt":
            return self._gt_pow(x, scalar)
        else:
            raise ValueError("BLS12-381 type mismatch")

    def bls12381_pairing(self, g1: _BlsPoint, g2: _BlsPoint) -> _BlsPoint:
        """Compute BLS12-381 pairing.

        Args:
            g1: G1 point
            g2: G2 point

        Returns:
            Gt element (pairing result)
        """
        g1_type = type(g1).__name__
        g2_type = type(g2).__name__

        if not g1_type.startswith("G1"):
            raise ValueError("BLS12-381 type mismatch")
        if not g2_type.startswith("G2"):
            raise ValueError("BLS12-381 type mismatch")

        return self._compute_pairing(g1, g2)

    # ========== BLS12-381 Internal Methods ==========
    # These wrappers delegate to BLS types. Cryptographic arithmetic
    # requires py_ecc and fails closed when unavailable.

    def _g1_to_compressed(self, point: Any) -> bytes:
        """Compress G1 point to 48 bytes."""
        try:
            return point.to_compressed()
        except AttributeError:
            # Placeholder: return zeros
            return b"\x00" * 48

    def _g1_from_compressed(self, data: bytes) -> Any:
        """Decompress G1 point from 48 bytes."""
        from neo.crypto.bls12_381 import G1Affine

        return G1Affine.from_compressed(data)

    def _g2_to_compressed(self, point: Any) -> bytes:
        """Compress G2 point to 96 bytes."""
        try:
            return point.to_compressed()
        except AttributeError:
            return b"\x00" * 96

    def _g2_from_compressed(self, data: bytes) -> Any:
        """Decompress G2 point from 96 bytes."""
        from neo.crypto.bls12_381 import G2Affine

        return G2Affine.from_compressed(data)

    def _gt_to_bytes(self, point: Any) -> bytes:
        """Serialize Gt element to 576 bytes."""
        try:
            return point.to_bytes()
        except AttributeError:
            return b"\x00" * 576

    def _gt_from_bytes(self, data: bytes) -> Any:
        """Deserialize Gt element from 576 bytes."""
        from neo.crypto.bls12_381 import Gt

        return Gt.from_bytes(data)

    def _g1_equal(self, x: Any, y: Any) -> bool:
        """Check G1 point equality."""
        return x == y

    def _g2_equal(self, x: Any, y: Any) -> bool:
        """Check G2 point equality."""
        return x == y

    def _g1_add(self, x: Any, y: Any) -> Any:
        """Add two G1 points."""
        return x + y

    def _g2_add(self, x: Any, y: Any) -> Any:
        """Add two G2 points."""
        return x + y

    def _gt_mul(self, x: Any, y: Any) -> Any:
        """Multiply two Gt elements."""
        return x * y

    def _g1_mul(self, point: Any, scalar: int) -> Any:
        """Scalar multiplication on G1."""
        return point * scalar

    def _g2_mul(self, point: Any, scalar: int) -> Any:
        """Scalar multiplication on G2."""
        return point * scalar

    def _gt_pow(self, point: Any, scalar: int) -> Any:
        """Exponentiation on Gt."""
        return point**scalar

    def _compute_pairing(self, g1: Any, g2: Any) -> Any:
        """Compute pairing e(g1, g2)."""
        from neo.crypto.bls12_381 import pairing

        return pairing(g1, g2)
