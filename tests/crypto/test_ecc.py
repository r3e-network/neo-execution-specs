"""Tests for ECC (Elliptic Curve Cryptography)."""

import pytest
from neo.crypto.ecc.curve import ECCurve, SECP256R1, SECP256K1
from neo.crypto.ecc.point import ECPoint


class TestECCurve:
    """Tests for ECCurve."""
    
    def test_secp256r1_params(self):
        """Test secp256r1 curve parameters."""
        assert SECP256R1.name == "secp256r1"
        assert SECP256R1.a == SECP256R1.p - 3  # a = -3 mod p
        assert SECP256R1.b != 0
        assert SECP256R1.n > 0
    
    def test_secp256k1_params(self):
        """Test secp256k1 curve parameters."""
        assert SECP256K1.name == "secp256k1"
        assert SECP256K1.a == 0
        assert SECP256K1.b == 7
        assert SECP256K1.n > 0
    
    def test_curve_immutable(self):
        """Test that curve is immutable (frozen dataclass)."""
        with pytest.raises(Exception):
            SECP256R1.name = "modified"
