"""Tests for Witness serialization."""

import pytest
from neo.network.payloads.witness import Witness


class TestWitnessSerialization:
    """Test Witness serialization."""
    
    def test_empty_witness(self):
        """Test empty witness."""
        w = Witness.empty()
        assert w.invocation_script == b""
        assert w.verification_script == b""
    
    def test_serialize_deserialize(self):
        """Test round-trip serialization."""
        w = Witness(
            invocation_script=b"\x01\x02\x03",
            verification_script=b"\x04\x05\x06\x07"
        )
        data = w.to_bytes()
        w2 = Witness.from_bytes(data)
        assert w2.invocation_script == w.invocation_script
        assert w2.verification_script == w.verification_script
    
    def test_size(self):
        """Test size calculation."""
        w = Witness(
            invocation_script=b"\x01\x02\x03",
            verification_script=b"\x04\x05"
        )
        # 1 byte for inv len + 3 bytes + 1 byte for ver len + 2 bytes
        assert w.size == 1 + 3 + 1 + 2
    
    def test_script_hash(self):
        """Test script hash calculation."""
        w = Witness(verification_script=b"\x55")
        h = w.script_hash
        assert len(h) == 20
