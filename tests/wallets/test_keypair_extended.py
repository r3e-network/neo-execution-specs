"""Tests for KeyPair."""

import pytest
from neo.wallets.key_pair import KeyPair


class TestKeyPairExtended:
    """Extended KeyPair tests."""
    
    def test_generate(self):
        """Test key generation."""
        kp = KeyPair.generate()
        assert kp.private_key is not None
        assert len(kp.private_key) == 32
