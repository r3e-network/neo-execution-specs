"""Tests for Signer."""

import pytest
from neo.network.payloads.signer import Signer
from neo.types.uint160 import UInt160


class TestSignerExtended:
    """Extended Signer tests."""
    
    def test_default_signer(self):
        """Test default signer."""
        s = Signer()
        assert s.scopes is not None
