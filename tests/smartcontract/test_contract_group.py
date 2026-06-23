"""Tests for ContractGroup."""

import pytest

from neo.smartcontract.manifest.contract_group import ContractGroup
from neo.types import UInt160


class TestContractGroup:
    """Tests for ContractGroup class."""
    
    def test_create_empty(self):
        """Test creating empty contract group."""
        group = ContractGroup()
        assert group.pubkey == b""
        assert group.signature == b""
    
    def test_create_with_data(self):
        """Test creating contract group with data."""
        pubkey = bytes(33)
        signature = bytes(64)
        group = ContractGroup(pubkey=pubkey, signature=signature)
        assert group.pubkey == pubkey
        assert group.signature == signature
    
    def test_is_valid_empty_returns_false(self):
        """Test that empty group is invalid."""
        group = ContractGroup()
        hash = UInt160(bytes(20))
        assert group.is_valid(hash) is False
    
    def test_is_valid_no_pubkey_returns_false(self):
        """Test that group without pubkey is invalid."""
        group = ContractGroup(signature=bytes(64))
        hash = UInt160(bytes(20))
        assert group.is_valid(hash) is False
    
    def test_is_valid_no_signature_returns_false(self):
        """Test that group without signature is invalid."""
        group = ContractGroup(pubkey=bytes(33))
        hash = UInt160(bytes(20))
        assert group.is_valid(hash) is False
    
    def test_to_json(self):
        """Test JSON serialization."""
        pubkey = bytes([1, 2, 3])
        signature = bytes([4, 5, 6])
        group = ContractGroup(pubkey=pubkey, signature=signature)
        json = group.to_json()
        assert json["pubkey"] == "010203"
        assert json["signature"] == "040506"
    
    def test_from_json(self):
        """Test JSON deserialization with a valid 64-byte signature.

        C# v3.10.0 ContractGroup.FromJson rejects any signature whose length
        is not 64, so the deserialized value must carry a 64-byte signature.
        """
        json = {
            "pubkey": "010203",
            "signature": bytes(range(64)).hex()
        }
        group = ContractGroup.from_json(json)
        assert group.pubkey == bytes([1, 2, 3])
        assert group.signature == bytes(range(64))

    def test_from_json_short_signature_rejected(self):
        """A signature shorter than 64 bytes is rejected (C# v3.10.0)."""
        json = {
            "pubkey": "010203",
            "signature": "040506"
        }
        with pytest.raises(ValueError, match="Signature length"):
            ContractGroup.from_json(json)

    def test_from_json_empty(self):
        """Empty/missing signature is rejected (length 0 != 64, C# v3.10.0)."""
        json = {}
        with pytest.raises(ValueError, match="Signature length"):
            ContractGroup.from_json(json)
    
    def test_roundtrip_json(self):
        """Test JSON roundtrip."""
        original = ContractGroup(
            pubkey=bytes(range(33)),
            signature=bytes(range(64))
        )
        json = original.to_json()
        restored = ContractGroup.from_json(json)
        assert restored.pubkey == original.pubkey
        assert restored.signature == original.signature
