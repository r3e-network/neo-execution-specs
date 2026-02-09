"""Tests for ECDSA signature verification."""

from neo.crypto.ecc.curve import SECP256R1
from neo.crypto.ecc.point import ECPoint
from neo.crypto.ecdsa import verify_signature


class TestECDSA:
    """Tests for ECDSA operations."""
    
    def test_verify_invalid_signature_length(self):
        """Test verification with invalid signature length."""
        point = ECPoint(SECP256R1.gx, SECP256R1.gy, SECP256R1)
        # Signature must be 64 bytes
        assert verify_signature(b"hash", b"short", point) is False
        assert verify_signature(b"hash", b"x" * 63, point) is False
        assert verify_signature(b"hash", b"x" * 65, point) is False
    
    def test_verify_zero_r_or_s(self):
        """Test verification with zero r or s values."""
        point = ECPoint(SECP256R1.gx, SECP256R1.gy, SECP256R1)
        # r = 0
        sig_zero_r = b"\x00" * 32 + b"\x01" * 32
        assert verify_signature(b"hash", sig_zero_r, point) is False
        # s = 0
        sig_zero_s = b"\x01" * 32 + b"\x00" * 32
        assert verify_signature(b"hash", sig_zero_s, point) is False
