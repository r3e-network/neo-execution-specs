"""Tests for transaction verification."""

from neo.ledger.transaction_verifier import TransactionVerifier
from neo.ledger.verify_result import VerifyResult
from neo.network.payloads.transaction import Transaction
from neo.network.payloads.signer import Signer
from neo.types.uint160 import UInt160


class TestTransactionVerifier:
    """Transaction verifier tests."""
    
    def test_verify_empty_script(self):
        """Empty script should fail."""
        tx = Transaction(script=b"")
        result = TransactionVerifier.verify_state_independent(tx)
        assert result == VerifyResult.INVALID
    
    def test_verify_no_signers(self):
        """No signers should fail."""
        tx = Transaction(script=b"\x40", signers=[])
        result = TransactionVerifier.verify_state_independent(tx)
        assert result == VerifyResult.INVALID
    
    def test_verify_valid_basic(self):
        """Valid basic transaction should pass."""
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(
            script=b"\x40",
            signers=[signer],
            system_fee=1000000,
            network_fee=100000,
            valid_until_block=1000
        )
        result = TransactionVerifier.verify_state_independent(tx)
        assert result == VerifyResult.SUCCEED
    
    def test_verify_negative_system_fee(self):
        """Negative system fee should fail."""
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(
            script=b"\x40",
            signers=[signer],
            system_fee=-1
        )
        result = TransactionVerifier.verify_state_independent(tx)
        assert result == VerifyResult.INVALID
    
    def test_verify_negative_network_fee(self):
        """Negative network fee should fail."""
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(
            script=b"\x40",
            signers=[signer],
            network_fee=-1
        )
        result = TransactionVerifier.verify_state_independent(tx)
        assert result == VerifyResult.INVALID
    
    def test_verify_duplicate_signers(self):
        """Duplicate signers should fail."""
        account = UInt160(b"\x01" * 20)
        signer1 = Signer(account=account)
        signer2 = Signer(account=account)
        tx = Transaction(
            script=b"\x40",
            signers=[signer1, signer2]
        )
        result = TransactionVerifier.verify_state_independent(tx)
        assert result == VerifyResult.INVALID
    
    def test_verify_invalid_version(self):
        """Invalid version should fail."""
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(
            version=1,
            script=b"\x40",
            signers=[signer]
        )
        result = TransactionVerifier.verify_state_independent(tx)
        assert result == VerifyResult.INVALID
