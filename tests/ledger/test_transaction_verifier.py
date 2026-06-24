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


class _ItemSnapshot:
    """Minimal value-bearing snapshot mirroring the native StorageItem shape."""

    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def add(self, key, item):
        self._data[key] = item

    def contains(self, key):
        return key in self._data

    def get_and_change(self, key, factory=None):
        item = self._data.get(key)
        if item is None:
            from neo.native.native_contract import StorageItem

            item = factory() if factory is not None else StorageItem()
            self._data[key] = item
        return item


def _persist_conflicting_tx(snapshot, conflict_hash, conflicting_signer):
    """Persist a tx that declares ``conflict_hash`` as a Conflicts attribute,
    populating the on-chain conflict stub + per-signer records."""
    from neo.native.ledger import LedgerContract
    from neo.native.native_contract import NativeContract
    from neo.network.payloads.block import Block
    from neo.network.payloads.transaction_attribute import ConflictsAttribute
    from neo.network.payloads.witness import Witness

    tx = Transaction(
        nonce=1,
        valid_until_block=1,
        signers=[conflicting_signer],
        attributes=[ConflictsAttribute(hash=conflict_hash)],
        script=b"\x51",
        witnesses=[Witness.empty()],
    )
    block = Block(index=3, witness=Witness.empty(), transactions=[tx])

    class _Engine:
        def __init__(self, snap, blk):
            self.snapshot = snap
            self.persisting_block = blk

    # Persist with the same singleton the verifier resolves so the storage-key
    # contract id matches.
    ledger = NativeContract.get_contract_by_name("LedgerContract")
    if ledger is None:
        ledger = LedgerContract()
    engine = _Engine(snapshot, block)
    ledger.on_persist(engine)
    ledger.post_persist(engine)


class TestTransactionVerifierConflicts:
    """Conflict detection mirrors LedgerContract.ContainsConflictHash."""

    def test_conflict_with_intersecting_signer_is_rejected(self):
        from neo.network.payloads.transaction_attribute import ConflictsAttribute

        snapshot = _ItemSnapshot()
        conflict_hash = bytes([0xCC]) * 32
        signer = Signer(account=UInt160(bytes([0x42]) * 20))
        _persist_conflicting_tx(snapshot, conflict_hash, signer)

        # A later tx whose hash collides AND shares the recorded signer conflicts.
        later = Transaction(
            nonce=99,
            valid_until_block=10,
            signers=[signer],
            attributes=[ConflictsAttribute(hash=conflict_hash)],
            script=b"\x51",
        )
        assert TransactionVerifier._has_conflicts(later, snapshot) is True

    def test_conflict_without_signer_intersection_is_not_rejected(self):
        from neo.network.payloads.transaction_attribute import ConflictsAttribute

        snapshot = _ItemSnapshot()
        conflict_hash = bytes([0xCC]) * 32
        recorded_signer = Signer(account=UInt160(bytes([0x42]) * 20))
        _persist_conflicting_tx(snapshot, conflict_hash, recorded_signer)

        # Different signer -> no intersection -> not a conflict (signer-keyed check,
        # unlike a plain contains_transaction lookup which would wrongly reject).
        other = Signer(account=UInt160(bytes([0x99]) * 20))
        later = Transaction(
            nonce=99,
            valid_until_block=10,
            signers=[other],
            attributes=[ConflictsAttribute(hash=conflict_hash)],
            script=b"\x51",
        )
        assert TransactionVerifier._has_conflicts(later, snapshot) is False

    def test_no_conflict_attribute_means_no_conflict(self):
        snapshot = _ItemSnapshot()
        signer = Signer(account=UInt160(b"\x01" * 20))
        tx = Transaction(script=b"\x51", signers=[signer], valid_until_block=10)
        assert TransactionVerifier._has_conflicts(tx, snapshot) is False
