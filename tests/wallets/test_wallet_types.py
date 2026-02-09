"""Tests for wallet types."""

from neo.wallets.key_pair import KeyPair


class TestKeyPair:
    """Tests for KeyPair."""
    
    def test_generate_random(self):
        """Test generating random key pair."""
        kp = KeyPair.generate()
        assert kp.private_key is not None
        assert len(kp.private_key) == 32
    
    def test_from_private_key(self):
        """Test creating from private key."""
        private_key = b'\x01' * 32
        kp = KeyPair.from_private_key(private_key)
        assert kp.private_key == private_key
    
    def test_public_key(self):
        """Test public key derivation."""
        private_key = b'\x01' * 32
        kp = KeyPair.from_private_key(private_key)
        assert kp.public_key is not None
