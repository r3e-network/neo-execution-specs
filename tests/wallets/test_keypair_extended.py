"""Tests for wallet module."""

from neo.wallets.key_pair import KeyPair


class TestKeyPair:
    """KeyPair tests."""
    
    def test_create_from_private_key(self):
        """Test creation from private key."""
        private_key = b"\x01" * 32
        kp = KeyPair.from_private_key(private_key)
        assert kp.private_key == private_key
    
    def test_public_key_generation(self):
        """Test public key is generated."""
        private_key = b"\x01" * 32
        kp = KeyPair.from_private_key(private_key)
        assert kp.public_key is not None
    
    def test_generate_random(self):
        """Test random key generation."""
        kp = KeyPair.generate()
        assert len(kp.private_key) == 32
        assert kp.public_key is not None
