"""Tests for Ed25519 signature verification."""

import pytest
from neo.crypto.ed25519 import ed25519_verify, HAS_ED25519


class TestEd25519:
    """Tests for Ed25519 operations."""
    
    def test_verify_invalid_pubkey_length(self):
        """Test verification with invalid public key length."""
        assert ed25519_verify(b"message", b"x" * 64, b"short") is False
        assert ed25519_verify(b"message", b"x" * 64, b"x" * 31) is False
        assert ed25519_verify(b"message", b"x" * 64, b"x" * 33) is False
    
    def test_verify_invalid_signature_length(self):
        """Test verification with invalid signature length."""
        assert ed25519_verify(b"message", b"short", b"x" * 32) is False
        assert ed25519_verify(b"message", b"x" * 63, b"x" * 32) is False
        assert ed25519_verify(b"message", b"x" * 65, b"x" * 32) is False
    
    @pytest.mark.skipif(not HAS_ED25519, reason="cryptography not installed")
    def test_verify_invalid_signature(self):
        """Test verification with invalid signature."""
        # Random invalid data
        result = ed25519_verify(b"message", b"x" * 64, b"y" * 32)
        assert result is False
