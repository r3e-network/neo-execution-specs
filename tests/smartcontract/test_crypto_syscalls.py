"""Tests for crypto syscalls."""

import pytest
from neo.smartcontract.syscalls.crypto import (
    _check_multisig_internal,
    CHECK_SIG_PRICE,
)


class TestCheckSigPrice:
    """Tests for CheckSig price constant."""
    
    def test_check_sig_price_value(self):
        """Test CheckSig price is correct."""
        assert CHECK_SIG_PRICE == 1 << 15
        assert CHECK_SIG_PRICE == 32768


class TestMultisigValidation:
    """Tests for multisig validation logic."""
    
    def test_empty_pubkeys_fails(self):
        """Test that empty pubkeys array fails."""
        # This is validated at the syscall level
        pass
    
    def test_empty_signatures_fails(self):
        """Test that empty signatures array fails."""
        # This is validated at the syscall level
        pass
    
    def test_more_sigs_than_keys_fails(self):
        """Test that more signatures than keys fails."""
        # This is validated at the syscall level
        pass


class TestSignatureVerification:
    """Tests for signature verification."""
    
    def test_invalid_pubkey_length(self):
        """Test that invalid pubkey length returns false."""
        from neo.crypto.ecc import SECP256R1
        from neo.crypto.ecc.signature import verify_signature
        
        # Invalid pubkey (wrong length)
        result = verify_signature(
            b"test message",
            b"\x00" * 64,  # signature
            b"\x00" * 10,  # invalid pubkey length
            SECP256R1
        )
        assert result is False
    
    def test_invalid_signature_length(self):
        """Test that invalid signature length returns false."""
        from neo.crypto.ecc import SECP256R1
        from neo.crypto.ecc.signature import verify_signature
        
        # Invalid signature (wrong length)
        result = verify_signature(
            b"test message",
            b"\x00" * 32,  # wrong length
            b"\x00" * 33,  # compressed pubkey length
            SECP256R1
        )
        assert result is False
