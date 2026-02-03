"""Extended tests for ECDSA signature operations."""

import pytest
from neo.crypto.ecc.curve import SECP256R1, SECP256K1, ECCurve
from neo.crypto.ecc.signature import verify_signature


class TestECCurve:
    """Tests for ECCurve class."""
    
    def test_secp256r1_name(self):
        """Test secp256r1 curve name."""
        assert SECP256R1.name == "secp256r1"
    
    def test_secp256k1_name(self):
        """Test secp256k1 curve name."""
        assert SECP256K1.name == "secp256k1"
    
    def test_secp256r1_parameters(self):
        """Test secp256r1 curve parameters."""
        assert SECP256R1.p > 0
        assert SECP256R1.n > 0
        assert SECP256R1.gx > 0
        assert SECP256R1.gy > 0
    
    def test_secp256k1_parameters(self):
        """Test secp256k1 curve parameters."""
        assert SECP256K1.p > 0
        assert SECP256K1.n > 0
        assert SECP256K1.a == 0
        assert SECP256K1.b == 7
    
    def test_curve_is_frozen(self):
        """Test that curve is immutable."""
        with pytest.raises(Exception):
            SECP256R1.name = "modified"


class TestSignatureVerification:
    """Tests for signature verification."""
    
    def test_invalid_pubkey_length(self):
        """Test verification with invalid pubkey length."""
        result = verify_signature(
            b"message",
            bytes(64),
            bytes(10),  # Invalid length
            SECP256R1
        )
        assert result is False
    
    def test_invalid_signature_length(self):
        """Test verification with invalid signature length."""
        result = verify_signature(
            b"message",
            bytes(32),  # Invalid length (should be 64)
            bytes(33),
            SECP256R1
        )
        assert result is False
    
    def test_valid_lengths_invalid_data(self):
        """Test verification with valid lengths but invalid data."""
        result = verify_signature(
            b"message",
            bytes(64),
            bytes(33),
            SECP256R1
        )
        assert result is False
