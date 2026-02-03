"""Tests for Account."""

import pytest
from neo.wallets.account import Account
from neo.types.uint160 import UInt160


class TestAccount:
    """Test Account."""
    
    def test_create(self):
        """Test create."""
        acc = Account(UInt160())
        assert acc is not None
