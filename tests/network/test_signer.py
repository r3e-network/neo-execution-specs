"""Tests for Signer serialization."""

import pytest
from neo.network.payloads.signer import Signer
from neo.network.payloads.witness_scope import WitnessScope
from neo.types.uint160 import UInt160


class TestSigner:
    """Tests for Signer."""
    
    def test_default_signer(self):
        """Test default signer values."""
        signer = Signer()
        assert signer.scopes == WitnessScope.CALLED_BY_ENTRY
        assert signer.allowed_contracts == []
        assert signer.allowed_groups == []
        assert signer.rules == []
    
    def test_signer_size_basic(self):
        """Test basic signer size."""
        signer = Signer(
            account=UInt160.ZERO,
            scopes=WitnessScope.CALLED_BY_ENTRY
        )
        # Account(20) + Scopes(1) = 21
        assert signer.size == 21
