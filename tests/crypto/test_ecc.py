"""Tests for ECC module."""

import pytest
from neo.crypto.ecc import ECPoint, derive_public_key


class TestECC:
    """ECC tests."""
    
    def test_derive_key(self):
        """Test key derivation."""
        pk = bytes(range(32))
        pub = derive_public_key(pk)
        assert pub is not None
