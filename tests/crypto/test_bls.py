"""Tests for BLS12-381 cryptographic operations."""

import pytest
from neo.crypto.bls12_381 import (
    G1Affine, G1Projective,
    G2Affine, G2Projective,
    Gt, Scalar, pairing
)


class TestG1:
    """Tests for G1 group operations."""
    
    def test_identity(self):
        """Test G1 identity element."""
        identity = G1Affine.identity()
        assert identity.is_identity()
    
    def test_generator(self):
        """Test G1 generator point."""
        g = G1Affine.generator()
        assert not g.is_identity()
        assert g.x != 0
        assert g.y != 0
    
    def test_compressed_roundtrip(self):
        """Test G1 compression/decompression."""
        g = G1Affine.generator()
        compressed = g.to_compressed()
        assert len(compressed) == 48
        
        recovered = G1Affine.from_compressed(compressed)
        assert recovered == g
    
    def test_identity_compressed(self):
        """Test identity point compression."""
        identity = G1Affine.identity()
        compressed = identity.to_compressed()
        assert len(compressed) == 48
        assert compressed[0] & 0xc0 == 0xc0  # compressed + infinity
        
        recovered = G1Affine.from_compressed(compressed)
        assert recovered.is_identity()
    
    def test_negation(self):
        """Test G1 point negation."""
        g = G1Affine.generator()
        neg_g = -g
        assert neg_g.x == g.x
        assert neg_g.y != g.y
    
    def test_projective_conversion(self):
        """Test affine/projective conversion."""
        g_affine = G1Affine.generator()
        g_proj = G1Projective.from_affine(g_affine)
        g_back = g_proj.to_affine()
        assert g_back == g_affine
    
    def test_addition(self):
        """Test G1 point addition."""
        g = G1Projective.generator()
        g2 = g + g
        assert not g2.is_identity()
        assert g2 != g
    
    def test_scalar_multiplication(self):
        """Test G1 scalar multiplication."""
        g = G1Projective.generator()
        g2 = g * 2
        g_plus_g = g + g
        assert g2 == g_plus_g
    
    def test_identity_addition(self):
        """Test addition with identity."""
        g = G1Projective.generator()
        identity = G1Projective.identity()
        assert (g + identity) == g
        assert (identity + g) == g


class TestG2:
    """Tests for G2 group operations."""
    
    def test_identity(self):
        """Test G2 identity element."""
        identity = G2Affine.identity()
        assert identity.is_identity()
    
    def test_identity_compressed(self):
        """Test G2 identity compression."""
        identity = G2Affine.identity()
        compressed = identity.to_compressed()
        assert len(compressed) == 96
        
        recovered = G2Affine.from_compressed(compressed)
        assert recovered.is_identity()
    
    def test_projective_identity(self):
        """Test G2 projective identity."""
        identity = G2Projective.identity()
        assert identity.is_identity()
    
    def test_negation(self):
        """Test G2 point negation."""
        identity = G2Affine.identity()
        neg = -identity
        assert neg.is_identity()


class TestScalar:
    """Tests for BLS12-381 scalar field."""
    
    def test_scalar_creation(self):
        """Test scalar creation."""
        s = Scalar(42)
        assert s.value == 42
    
    def test_scalar_modular(self):
        """Test scalar modular reduction."""
        from neo.crypto.bls12_381.scalar import SCALAR_MODULUS
        s = Scalar(SCALAR_MODULUS + 1)
        assert s.value == 1


class TestGt:
    """Tests for Gt group operations."""
    
    def test_identity(self):
        """Test Gt identity element."""
        identity = Gt.identity()
        assert identity.is_identity()
    
    def test_from_bytes(self):
        """Test Gt deserialization."""
        data = bytes(576)
        gt = Gt(data)
        assert len(gt.to_bytes()) == 576


class TestPairing:
    """Tests for BLS12-381 pairing."""
    
    def test_pairing_identity_g1(self):
        """Test pairing with G1 identity."""
        g1_id = G1Affine.identity()
        g2 = G2Affine.identity()
        result = pairing(g1_id, g2)
        assert result.is_identity()
    
    def test_pairing_identity_g2(self):
        """Test pairing with G2 identity."""
        g1 = G1Affine.generator()
        g2_id = G2Affine.identity()
        result = pairing(g1, g2_id)
        assert result.is_identity()
    
    def test_pairing_projective(self):
        """Test pairing with projective points."""
        g1 = G1Projective.generator()
        g2 = G2Projective.identity()
        result = pairing(g1, g2)
        assert result.is_identity()
