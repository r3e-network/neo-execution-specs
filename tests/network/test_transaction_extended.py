"""Tests for network payloads."""

import pytest
from neo.network.payloads.transaction import Transaction
from neo.network.payloads.signer import Signer
from neo.network.payloads.witness import Witness
from neo.types.uint160 import UInt160


class TestTransactionExtended:
    """Extended transaction tests."""
    
    def test_sender(self):
        """Test sender property."""
        account = UInt160(b"\x01" * 20)
        signer = Signer(account=account)
        tx = Transaction(script=b"\x40", signers=[signer])
        assert tx.sender == bytes(account)
    
    def test_hash_deterministic(self):
        """Test hash is deterministic."""
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(script=b"\x40", signers=[signer])
        assert tx.hash == tx.hash
