"""Tests for KeyBuilder."""

import pytest
from neo.smartcontract.key_builder import KeyBuilder


class TestKeyBuilder:
    """Test KeyBuilder."""
    
    def test_create_key(self):
        """Test key creation."""
        kb = KeyBuilder(1, 2)
        assert kb is not None
