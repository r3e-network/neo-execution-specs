"""Tests for witness scope."""

import pytest
from neo.network.payloads.witness_scope import WitnessScope


class TestWitnessScope:
    """Witness scope tests."""
    
    def test_none(self):
        """Test NONE scope."""
        assert WitnessScope.NONE == 0
    
    def test_global(self):
        """Test GLOBAL scope."""
        assert WitnessScope.GLOBAL == 0x80
    
    def test_called_by_entry(self):
        """Test CALLED_BY_ENTRY scope."""
        assert WitnessScope.CALLED_BY_ENTRY == 0x01
