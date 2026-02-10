"""Tests for CryptoLib secp256k1 public key recovery.

Validates recover_secp256k1 with invalid inputs and an end-to-end
sign-then-recover flow using the ``cryptography`` library.
"""

import pytest

from neo.native.crypto_lib import CryptoLib
from neo.crypto.ecc.curve import SECP256K1
from neo.crypto.ecc.point import ECPoint


@pytest.fixture
def crypto() -> CryptoLib:
    return CryptoLib()


class TestRecoverInvalidInputs:
    """recover_secp256k1 must return None for malformed inputs."""

    def test_empty_signature(self, crypto: CryptoLib):
        msg_hash = b"\x01" * 32
        assert crypto.recover_secp256k1(msg_hash, b"") is None

    def test_short_signature(self, crypto: CryptoLib):
        msg_hash = b"\x01" * 32
        assert crypto.recover_secp256k1(msg_hash, b"\x00" * 63) is None

    def test_too_long_signature(self, crypto: CryptoLib):
        msg_hash = b"\x01" * 32
        assert crypto.recover_secp256k1(msg_hash, b"\x00" * 66) is None

    def test_invalid_v_value(self, crypto: CryptoLib):
        """v byte outside {27,28} (after normalization) should fail."""
        msg_hash = b"\x01" * 32
        # r and s are non-zero, v = 30 => normalized v = 3, not in {0,1}
        sig = b"\x01" * 32 + b"\x01" * 32 + bytes([30])
        assert crypto.recover_secp256k1(msg_hash, sig) is None

    def test_zero_r_returns_none(self, crypto: CryptoLib):
        """r = 0 is outside [1, n-1]."""
        msg_hash = b"\x01" * 32
        sig = b"\x00" * 32 + b"\x01" * 32 + bytes([27])
        # This should fail during modular inverse of r
        result = crypto.recover_secp256k1(msg_hash, sig)
        assert result is None


class TestRecoverEndToEnd:
    """End-to-end sign-then-recover using the cryptography library."""

    @staticmethod
    def _make_k1_keypair():
        """Generate a secp256k1 key pair."""
        from cryptography.hazmat.primitives.asymmetric import ec
        private = ec.generate_private_key(ec.SECP256K1())
        nums = private.public_key().public_numbers()
        point = ECPoint(nums.x, nums.y, SECP256K1)
        compressed = point.encode(compressed=True)
        return private, compressed, nums

    @staticmethod
    def _sign_k1_recoverable(private_key, msg_hash: bytes):
        """Sign with secp256k1 and return (r, s, v) for recovery."""
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        from cryptography.hazmat.primitives import hashes
        import hashlib

        der_sig = private_key.sign(msg_hash, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        r, s = utils.decode_dss_signature(der_sig)
        return r, s

    def test_recover_matches_pubkey(self, crypto: CryptoLib):
        """Recover public key from signature and verify it matches."""
        import hashlib

        private, expected_pubkey, nums = self._make_k1_keypair()
        msg = b"Neo N3 recovery test"
        msg_hash = hashlib.sha256(msg).digest()

        r, s = self._sign_k1_recoverable(private, msg_hash)
        r_bytes = r.to_bytes(32, "big")
        s_bytes = s.to_bytes(32, "big")

        # Try both recovery IDs (v=27 and v=28)
        for v in (27, 28):
            sig65 = r_bytes + s_bytes + bytes([v])
            recovered = crypto.recover_secp256k1(msg_hash, sig65)
            if recovered is not None and recovered == expected_pubkey:
                return  # success

        pytest.fail("Could not recover the correct public key with either v value")

    def test_recover_wrong_hash_gives_different_key(self, crypto: CryptoLib):
        """Recovery with wrong hash should yield a different public key."""
        import hashlib

        private, expected_pubkey, _ = self._make_k1_keypair()
        msg_hash = hashlib.sha256(b"correct message").digest()
        wrong_hash = hashlib.sha256(b"wrong message").digest()

        r, s = self._sign_k1_recoverable(private, msg_hash)
        r_bytes = r.to_bytes(32, "big")
        s_bytes = s.to_bytes(32, "big")

        for v in (27, 28):
            sig65 = r_bytes + s_bytes + bytes([v])
            recovered = crypto.recover_secp256k1(wrong_hash, sig65)
            if recovered is not None:
                assert recovered != expected_pubkey
