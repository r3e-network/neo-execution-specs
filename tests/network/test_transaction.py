"""Tests for Transaction serialization."""

from neo.network.payloads.transaction import Transaction, HEADER_SIZE


class TestTransaction:
    """Tests for Transaction."""
    
    def test_default_transaction(self):
        """Test default transaction values."""
        tx = Transaction()
        assert tx.version == 0
        assert tx.nonce == 0
        assert tx.system_fee == 0
        assert tx.network_fee == 0
        assert tx.valid_until_block == 0
        assert tx.signers == []
        assert tx.attributes == []
        assert tx.script == b""
        assert tx.witnesses == []
    
    def test_header_size_constant(self):
        """Test header size constant."""
        # Version(1) + Nonce(4) + SystemFee(8) + NetworkFee(8) + ValidUntilBlock(4)
        assert HEADER_SIZE == 25
    
    def test_sender_empty(self):
        """Test sender with no signers."""
        tx = Transaction()
        assert tx.sender == b"\x00" * 20
