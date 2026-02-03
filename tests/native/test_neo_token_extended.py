"""Tests for NeoToken extended."""

import pytest
from neo.native.neo_token import NeoToken


class TestNeoTokenExtended:
    """Test NeoToken."""
    
    def test_total_amount(self):
        """Test total amount."""
        neo = NeoToken()
        assert neo.total_amount == 100_000_000
