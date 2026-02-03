"""Tests for NativeContract base."""

import pytest
from neo.native.policy import PolicyContract


class TestNativeContractBase:
    """Test NativeContract base class."""
    
    def test_hash_property(self):
        """Test hash property exists."""
        nc = PolicyContract()
        assert hasattr(nc, 'hash')
