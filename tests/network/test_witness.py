"""Tests for Witness serialization."""

import pytest
from neo.network.payloads.witness import Witness, _get_var_size


class TestWitness:
    """Tests for Witness."""
    
    def test_empty_witness(self):
        """Test creating empty witness."""
        w = Witness.empty()
        assert w.invocation_script == b""
        assert w.verification_script == b""
    
    def test_witness_size(self):
        """Test witness size calculation."""
        w = Witness(
            invocation_script=b"inv",
            verification_script=b"ver"
        )
        # Size = var_size(3) + 3 + var_size(3) + 3 = 1+3+1+3 = 8
        assert w.size == 8
    
    def test_script_hash(self):
        """Test script hash calculation."""
        w = Witness(verification_script=b"test")
        h = w.script_hash
        assert len(h) == 20
        # Same script should give same hash
        assert w.script_hash == h
