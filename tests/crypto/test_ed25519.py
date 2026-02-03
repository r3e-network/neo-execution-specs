"""Tests for Ed25519 signature verification."""

import pytest
from neo.crypto.ed25519 import ed25519_verify, HAS_ED25519


class TestEd25519:
    """Tests for Ed25519 signature verification."""
    
    def test_invalid_pubkey_length(self):
        """Test that invalid pubkey length returns False."""
        assert not ed25519_verify(b"message", b"x" * 64, b"short")
        assert not ed25519_verify(b"message", b"x" * 64, b"x" * 31)
        assert not ed25519_verify(b"message", b"x" * 64, b"x" * 33)
    
    def test_invalid_signature_length(self):
        """Test that invalid signature length returns False."""
        assert not ed25519_verify(b"message", b"short", b"x" * 32)
        assert not ed25519_verify(b"message", b"x" * 63, b"x" * 32)
        assert not ed25519_verify(b"message", b"x" * 65, b"x" * 32)
    
    def test_invalid_pubkey_bytes(self):
        """Test that invalid pubkey bytes returns False."""
        # All zeros is not a valid Ed25519 public key
        result = ed25519_verify(b"message", b"x" * 64, b"\x00" * 32)
        assert not result
    
    @pytest.mark.skipif(not HAS_ED25519, reason="cryptography library not available")
    def test_valid_signature(self):
        """Test verification of a valid signature."""
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            # Generate a key pair
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Sign a message
            message = b"Hello, Neo!"
            signature = private_key.sign(message)
            
            # Get raw bytes
            pubkey_bytes = public_key.public_bytes_raw()
            
            # Verify
            assert ed25519_verify(message, signature, pubkey_bytes)
        except ImportError:
            pytest.skip("cryptography library not available")
    
    @pytest.mark.skipif(not HAS_ED25519, reason="cryptography library not available")
    def test_invalid_signature(self):
        """Test that invalid signature returns False."""
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            message = b"Hello, Neo!"
            signature = private_key.sign(message)
            
            pubkey_bytes = public_key.public_bytes_raw()
            
            # Tamper with signature
            bad_sig = bytes([signature[0] ^ 0xff]) + signature[1:]
            assert not ed25519_verify(message, bad_sig, pubkey_bytes)
        except ImportError:
            pytest.skip("cryptography library not available")
    
    @pytest.mark.skipif(not HAS_ED25519, reason="cryptography library not available")
    def test_wrong_message(self):
        """Test that wrong message returns False."""
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            message = b"Hello, Neo!"
            signature = private_key.sign(message)
            
            pubkey_bytes = public_key.public_bytes_raw()
            
            # Different message
            assert not ed25519_verify(b"Different message", signature, pubkey_bytes)
        except ImportError:
            pytest.skip("cryptography library not available")
    
    def test_empty_message(self):
        """Test with empty message."""
        # Should not crash, just return False for invalid key
        result = ed25519_verify(b"", b"x" * 64, b"x" * 32)
        assert isinstance(result, bool)
