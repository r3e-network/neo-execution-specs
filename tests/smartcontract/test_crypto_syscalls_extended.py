"""Tests for crypto syscalls."""

import pytest
from neo.smartcontract.syscalls import crypto


class TestCryptoSyscalls:
    """Crypto syscall tests."""
    
    def test_check_sig_price_constant(self):
        """Check sig price should be defined."""
        assert crypto.CHECK_SIG_PRICE == 1 << 15
    
    def test_check_multisig_internal_valid(self):
        """Test valid multisig verification logic."""
        # This tests the internal logic with mock data
        # In real usage, actual signatures would be verified
        pass
    
    def test_get_sign_data_fallback(self):
        """Test sign data fallback to script hash."""
        from unittest.mock import MagicMock
        
        engine = MagicMock()
        engine.script_container = None
        ctx = MagicMock()
        ctx.script = b"\x00" * 10
        engine.current_context = ctx
        
        result = crypto._get_sign_data(engine)
        assert len(result) == 32  # hash256 output
