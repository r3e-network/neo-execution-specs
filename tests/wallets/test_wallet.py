"""Tests for wallet module."""

import pytest
from neo.wallets import KeyPair, Account, Wallet
from neo.wallets.key_pair import base58_encode, base58_decode


class TestKeyPair:
    """KeyPair tests."""
    
    def test_generate(self):
        """Test key generation."""
        kp = KeyPair.generate()
        assert len(kp.private_key) == 32
    
    def test_from_private_key(self):
        """Test from private key."""
        pk = bytes(range(32))
        kp = KeyPair.from_private_key(pk)
        assert kp.private_key == pk


class TestBase58:
    """Base58 tests."""
    
    def test_encode_decode(self):
        """Test encode/decode."""
        data = b"hello"
        encoded = base58_encode(data)
        decoded = base58_decode(encoded)
        assert decoded == data
    
    def test_leading_zeros(self):
        """Test leading zeros."""
        data = b"\x00\x00hello"
        encoded = base58_encode(data)
        assert encoded.startswith("11")


class TestWallet:
    """Wallet tests."""
    
    def test_create_account(self):
        """Test account creation."""
        wallet = Wallet()
        account = wallet.create_account("test")
        assert account.label == "test"
        assert account.has_key
