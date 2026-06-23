"""Tests for Ledger native contract."""

from __future__ import annotations

from typing import Any

from neo.native.ledger import (
    LedgerContract,
    TrimmedBlock,
)
from neo.native.native_contract import StorageItem
from neo.network.payloads.block import Block
from neo.network.payloads.signer import Signer
from neo.network.payloads.transaction import Transaction
from neo.network.payloads.witness import Witness
from neo.types import UInt160


class _Snapshot:
    def __init__(self) -> None:
        self._data: dict[Any, StorageItem] = {}

    def get(self, key: Any) -> StorageItem | None:
        return self._data.get(key)

    def add(self, key: Any, item: StorageItem) -> None:
        self._data[key] = item

    def contains(self, key: Any) -> bool:
        return key in self._data

    def get_and_change(self, key: Any, factory=None) -> StorageItem:
        item = self._data.get(key)
        if item is None:
            item = factory() if factory is not None else StorageItem()
            self._data[key] = item
        return item


class _Engine:
    def __init__(self, snapshot: _Snapshot, persisting_block: Block | None = None) -> None:
        self.snapshot = snapshot
        self.persisting_block = persisting_block


def _tx(nonce: int, account_byte: int) -> Transaction:
    signer = Signer(account=UInt160(bytes([account_byte]) * 20))
    return Transaction(
        nonce=nonce,
        valid_until_block=1,
        signers=[signer],
        script=b"\x51",  # PUSH1
        witnesses=[Witness.empty()],
    )


def _block_with_transactions(index: int, txs: list[Transaction]) -> Block:
    return Block(index=index, witness=Witness.empty(), transactions=txs)


class TestLedgerContract:
    """Tests for LedgerContract."""
    
    def test_name(self):
        """Test contract name."""
        ledger = LedgerContract()
        assert ledger.name == "LedgerContract"

    def test_get_transaction_from_block_returns_indexed_transaction(self):
        ledger = LedgerContract()
        snapshot = _Snapshot()

        tx1 = _tx(1, 0x11)
        tx2 = _tx(2, 0x22)
        block = _block_with_transactions(index=77, txs=[tx1, tx2])
        engine = _Engine(snapshot=snapshot, persisting_block=block)

        # on_persist stores the TrimmedBlock + each transaction; post_persist makes
        # the block the chain tip so it is traceable.
        ledger.on_persist(engine)
        ledger.post_persist(engine)

        result = ledger.get_transaction_from_block(engine, block.index.to_bytes(4, "little"), 1)
        assert result is not None
        assert result.hash == tx2.hash

        # The stored block is now a TrimmedBlock (header + tx hashes), not the full
        # block (state-root critical, matching C# TrimmedBlock.Create(block)).
        trimmed = ledger.get_block(engine, block.index.to_bytes(4, "little"))
        assert isinstance(trimmed, TrimmedBlock)
        assert [bytes(h) for h in trimmed.hashes] == [tx1.hash.data, tx2.hash.data]

    def test_get_transaction_from_block_out_of_range_tx_index_faults(self):
        ledger = LedgerContract()
        snapshot = _Snapshot()

        tx1 = _tx(1, 0x11)
        block = _block_with_transactions(index=5, txs=[tx1])
        engine = _Engine(snapshot=snapshot, persisting_block=block)

        ledger.on_persist(engine)
        ledger.post_persist(engine)

        import pytest

        # Out-of-range txIndex faults (C# throws ArgumentOutOfRangeException), it
        # does not return None.
        with pytest.raises(ValueError):
            ledger.get_transaction_from_block(engine, block.hash.data, 5)
        with pytest.raises(ValueError):
            ledger.get_transaction_from_block(engine, block.hash.data, -1)

    def test_on_persist_stores_transactions_retrievable_by_hash(self):
        ledger = LedgerContract()
        snapshot = _Snapshot()

        tx1 = _tx(10, 0xAA)
        tx2 = _tx(20, 0xBB)
        block = _block_with_transactions(index=88, txs=[tx1, tx2])
        engine = _Engine(snapshot=snapshot, persisting_block=block)

        ledger.on_persist(engine)
        # post_persist sets the current block; without it the stored tx's block is
        # in the future relative to the (zero) current index and IsTraceableBlock
        # would hide it (matching C#).
        ledger.post_persist(engine)

        result = ledger.get_transaction(engine, tx1.hash)
        assert result is not None
        assert result.hash == tx1.hash

    def test_on_persist_writes_conflict_stubs_hidden_from_get_transaction(self):
        from neo.native.ledger import PREFIX_TRANSACTION
        from neo.network.payloads.transaction_attribute import ConflictsAttribute

        ledger = LedgerContract()
        snapshot = _Snapshot()

        conflict_hash = bytes([0xCC]) * 32
        signer = Signer(account=UInt160(bytes([0x42]) * 20))
        tx = Transaction(
            nonce=7,
            valid_until_block=1,
            signers=[signer],
            attributes=[ConflictsAttribute(hash=conflict_hash)],
            script=b"\x51",
            witnesses=[Witness.empty()],
        )
        block = _block_with_transactions(index=3, txs=[tx])
        engine = _Engine(snapshot=snapshot, persisting_block=block)

        ledger.on_persist(engine)
        ledger.post_persist(engine)

        # The conflict stub is stored under Prefix_Transaction|conflict_hash and
        # Prefix_Transaction|conflict_hash|signer.account.
        from neo.types import UInt256

        stub_key = ledger._create_storage_key(PREFIX_TRANSACTION, conflict_hash)  # noqa: SLF001
        assert snapshot.get(stub_key) is not None
        signer_key = ledger._create_storage_key(  # noqa: SLF001
            PREFIX_TRANSACTION, conflict_hash, signer.account.data
        )
        assert snapshot.get(signer_key) is not None

        # But the stub (Transaction == null) is hidden from the transaction getters.
        conflict_uint = UInt256(conflict_hash)
        assert ledger.get_transaction(engine, conflict_uint) is None
        assert ledger.get_transaction_height(engine, conflict_uint) == -1
        assert ledger.get_transaction_vm_state(engine, conflict_uint) == 0
        assert ledger.contains_transaction(snapshot, conflict_uint) is False
