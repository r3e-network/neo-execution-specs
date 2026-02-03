"""Tests for ECPoint."""

import pytest
from neo.types.ec_point import ECPoint


class TestECPoint:
    """Test ECPoint functionality."""
    
    def test_infinity(self):
        """Test infinity point."""
        p = ECPoint.infinity()
        assert p.x == 0 and p.y == 0
    
    def test_decode_compressed(self):
        """Test decode compressed bytes."""
        data = bytes([0x02]) + bytes(32)
        p = ECPoint.decode(data)
        assert p is not None
