"""Tests for ECPoint."""

from neo.crypto.ecc.curve import SECP256R1
from neo.crypto.ecc.point import ECPoint


class TestECPoint:
    """Tests for ECPoint."""
    
    def test_infinity_point(self):
        """Test point at infinity."""
        point = ECPoint(0, 0, SECP256R1)
        assert point.is_infinity
    
    def test_non_infinity_point(self):
        """Test non-infinity point."""
        point = ECPoint(SECP256R1.gx, SECP256R1.gy, SECP256R1)
        assert not point.is_infinity
    
    def test_encode_infinity(self):
        """Test encoding infinity point."""
        point = ECPoint(0, 0, SECP256R1)
        assert point.encode() == b"\x00"
    
    def test_encode_compressed_even_y(self):
        """Test compressed encoding with even Y."""
        # Use generator point
        point = ECPoint(SECP256R1.gx, SECP256R1.gy, SECP256R1)
        encoded = point.encode(compressed=True)
        assert len(encoded) == 33
        assert encoded[0] in (0x02, 0x03)
    
    def test_encode_uncompressed(self):
        """Test uncompressed encoding."""
        point = ECPoint(SECP256R1.gx, SECP256R1.gy, SECP256R1)
        encoded = point.encode(compressed=False)
        assert len(encoded) == 65
        assert encoded[0] == 0x04
