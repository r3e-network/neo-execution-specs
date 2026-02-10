"""Tests for CryptoLib ECDSA signature verification.

Uses the ``cryptography`` library to generate real key pairs and signatures,
then verifies them through the CryptoLib.verify_with_ecdsa path.
"""

import pytest

from neo.native.crypto_lib import CryptoLib, NamedCurveHash
from neo.crypto.ecc.curve import SECP256R1, SECP256K1
from neo.crypto.ecc.point import ECPoint


@pytest.fixture
def crypto() -> CryptoLib:
    return CryptoLib()


def _make_r1_keypair():
    """Generate a secp256r1 key pair and return (private_key, compressed_pubkey)."""
    from cryptography.hazmat.primitives.asymmetric import ec

    private = ec.generate_private_key(ec.SECP256R1())
    nums = private.public_key().public_numbers()
    point = ECPoint(nums.x, nums.y, SECP256R1)
    pubkey_bytes = point.encode(compressed=True)
    return private, pubkey_bytes


def _sign_r1(private_key, message: bytes) -> bytes:
    """Sign *message* with secp256r1/SHA-256 and return raw r||s (64 bytes)."""
    from cryptography.hazmat.primitives.asymmetric import ec, utils
    from cryptography.hazmat.primitives import hashes

    der_sig = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der_sig)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


class TestVerifyWithEcdsaR1:
    """Verify secp256r1 + SHA-256 signatures through CryptoLib."""

    def test_valid_signature(self, crypto: CryptoLib):
        private, pubkey = _make_r1_keypair()
        message = b"Neo N3 test message"
        signature = _sign_r1(private, message)

        assert crypto.verify_with_ecdsa(
            message, pubkey, signature, NamedCurveHash.secp256r1SHA256
        ) is True

    def test_different_messages_produce_different_sigs(self, crypto: CryptoLib):
        private, pubkey = _make_r1_keypair()
        sig_a = _sign_r1(private, b"message A")
        sig_b = _sign_r1(private, b"message B")
        assert sig_a != sig_b

    def test_invalid_signature_returns_false(self, crypto: CryptoLib):
        private, pubkey = _make_r1_keypair()
        message = b"Neo N3 test message"
        bad_sig = b"\x00" * 64

        assert crypto.verify_with_ecdsa(
            message, pubkey, bad_sig, NamedCurveHash.secp256r1SHA256
        ) is False

    def test_tampered_signature_returns_false(self, crypto: CryptoLib):
        private, pubkey = _make_r1_keypair()
        message = b"Neo N3 test message"
        signature = bytearray(_sign_r1(private, message))
        signature[0] ^= 0xFF  # flip first byte
        signature = bytes(signature)

        assert crypto.verify_with_ecdsa(
            message, pubkey, signature, NamedCurveHash.secp256r1SHA256
        ) is False

    def test_wrong_message_returns_false(self, crypto: CryptoLib):
        private, pubkey = _make_r1_keypair()
        signature = _sign_r1(private, b"correct message")

        assert crypto.verify_with_ecdsa(
            b"wrong message", pubkey, signature, NamedCurveHash.secp256r1SHA256
        ) is False

    def test_wrong_pubkey_returns_false(self, crypto: CryptoLib):
        priv1, pub1 = _make_r1_keypair()
        _priv2, pub2 = _make_r1_keypair()
        message = b"Neo N3 test message"
        signature = _sign_r1(priv1, message)

        # Verify with the wrong public key
        assert crypto.verify_with_ecdsa(
            message, pub2, signature, NamedCurveHash.secp256r1SHA256
        ) is False

    def test_short_signature_returns_false(self, crypto: CryptoLib):
        _private, pubkey = _make_r1_keypair()
        assert crypto.verify_with_ecdsa(
            b"msg", pubkey, b"\x01" * 63, NamedCurveHash.secp256r1SHA256
        ) is False

    def test_long_signature_returns_false(self, crypto: CryptoLib):
        _private, pubkey = _make_r1_keypair()
        assert crypto.verify_with_ecdsa(
            b"msg", pubkey, b"\x01" * 65, NamedCurveHash.secp256r1SHA256
        ) is False


def _make_k1_keypair():
    """Generate a secp256k1 key pair and return (private_key, compressed_pubkey)."""
    from cryptography.hazmat.primitives.asymmetric import ec

    private = ec.generate_private_key(ec.SECP256K1())
    nums = private.public_key().public_numbers()
    point = ECPoint(nums.x, nums.y, SECP256K1)
    pubkey_bytes = point.encode(compressed=True)
    return private, pubkey_bytes


def _sign_k1(private_key, message: bytes) -> bytes:
    """Sign *message* with secp256k1/SHA-256 and return raw r||s (64 bytes)."""
    from cryptography.hazmat.primitives.asymmetric import ec, utils
    from cryptography.hazmat.primitives import hashes

    der_sig = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der_sig)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


class TestVerifyWithEcdsaK1:
    """Verify secp256k1 + SHA-256 signatures through CryptoLib."""

    def test_valid_signature(self, crypto: CryptoLib):
        private, pubkey = _make_k1_keypair()
        message = b"Neo N3 secp256k1 test"
        signature = _sign_k1(private, message)

        assert crypto.verify_with_ecdsa(
            message, pubkey, signature, NamedCurveHash.secp256k1SHA256
        ) is True

    def test_invalid_signature_returns_false(self, crypto: CryptoLib):
        _private, pubkey = _make_k1_keypair()
        assert crypto.verify_with_ecdsa(
            b"msg", pubkey, b"\x00" * 64, NamedCurveHash.secp256k1SHA256
        ) is False

    def test_tampered_signature_returns_false(self, crypto: CryptoLib):
        private, pubkey = _make_k1_keypair()
        message = b"Neo N3 secp256k1 test"
        signature = bytearray(_sign_k1(private, message))
        signature[0] ^= 0xFF
        signature = bytes(signature)

        assert crypto.verify_with_ecdsa(
            message, pubkey, signature, NamedCurveHash.secp256k1SHA256
        ) is False

    def test_wrong_message_returns_false(self, crypto: CryptoLib):
        private, pubkey = _make_k1_keypair()
        signature = _sign_k1(private, b"correct message")

        assert crypto.verify_with_ecdsa(
            b"wrong message", pubkey, signature, NamedCurveHash.secp256k1SHA256
        ) is False

    def test_wrong_pubkey_returns_false(self, crypto: CryptoLib):
        priv1, _pub1 = _make_k1_keypair()
        _priv2, pub2 = _make_k1_keypair()
        message = b"Neo N3 secp256k1 test"
        signature = _sign_k1(priv1, message)

        assert crypto.verify_with_ecdsa(
            message, pub2, signature, NamedCurveHash.secp256k1SHA256
        ) is False


def _keccak256(data: bytes) -> bytes:
    """Compute Keccak-256 hash."""
    from Crypto.Hash import keccak
    h = keccak.new(digest_bits=256)
    h.update(data)
    return h.digest()


def _sign_with_prehash(private_key, msg_hash: bytes) -> bytes:
    """Sign a pre-hashed message and return raw r||s (64 bytes)."""
    from cryptography.hazmat.primitives.asymmetric import ec, utils
    from cryptography.hazmat.primitives import hashes

    der_sig = private_key.sign(
        msg_hash, ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )
    r, s = utils.decode_dss_signature(der_sig)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


class TestVerifyWithKeccak256:
    """Verify Keccak-256 hash variants through CryptoLib."""

    def test_k1_keccak256_valid(self, crypto: CryptoLib):
        private, pubkey = _make_k1_keypair()
        message = b"Neo N3 keccak256 test"
        # CryptoLib hashes with keccak256 internally, so sign the keccak hash
        signature = _sign_with_prehash(private, _keccak256(message))

        assert crypto.verify_with_ecdsa(
            message, pubkey, signature, NamedCurveHash.secp256k1Keccak256
        ) is True

    def test_r1_keccak256_valid(self, crypto: CryptoLib):
        private, pubkey = _make_r1_keypair()
        message = b"Neo N3 keccak256 r1 test"
        signature = _sign_with_prehash(private, _keccak256(message))

        assert crypto.verify_with_ecdsa(
            message, pubkey, signature, NamedCurveHash.secp256r1Keccak256
        ) is True

    def test_keccak256_wrong_message(self, crypto: CryptoLib):
        private, pubkey = _make_k1_keypair()
        signature = _sign_with_prehash(private, _keccak256(b"correct"))

        assert crypto.verify_with_ecdsa(
            b"wrong", pubkey, signature, NamedCurveHash.secp256k1Keccak256
        ) is False


class TestVerifyWrongCurve:
    """Passing a signature verified against the wrong curve should fail."""

    def test_r1_sig_with_k1_curve_returns_false(self, crypto: CryptoLib):
        private, pubkey = _make_r1_keypair()
        message = b"cross-curve test"
        signature = _sign_r1(private, message)

        # The pubkey is a valid r1 point; asking for k1 should fail
        # because the point won't decode on the k1 curve.
        assert crypto.verify_with_ecdsa(
            message, pubkey, signature, NamedCurveHash.secp256k1SHA256
        ) is False
