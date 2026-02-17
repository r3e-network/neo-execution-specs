"""Tests for Ledger native contract."""

from __future__ import annotations

from typing import Any

from neo.io.binary_writer import BinaryWriter
from neo.native.ledger import LedgerContract, PREFIX_BLOCK, PREFIX_BLOCK_HASH
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


def _serialize_block(block: Block) -> bytes:
    writer = BinaryWriter()
    block.serialize(writer)
    return writer.to_bytes()


class TestLedgerContract:
    """Tests for LedgerContract."""
    
    def test_name(self):
        """Test contract name."""
        ledger = LedgerContract()
        assert ledger.name == "LedgerContract"

    def test_get_transaction_from_block_returns_indexed_transaction_for_stored_block_bytes(self):
        ledger = LedgerContract()
        snapshot = _Snapshot()
        engine = _Engine(snapshot=snapshot)

        tx1 = _tx(1, 0x11)
        tx2 = _tx(2, 0x22)
        block = _block_with_transactions(index=77, txs=[tx1, tx2])

        hash_key = ledger._create_storage_key(PREFIX_BLOCK_HASH, block.index)  # noqa: SLF001
        snapshot.add(hash_key, StorageItem(block.hash.data))

        block_key = ledger._create_storage_key(PREFIX_BLOCK, block.hash.data)  # noqa: SLF001
        snapshot.add(block_key, StorageItem(_serialize_block(block)))

        result = ledger.get_transaction_from_block(engine, block.index.to_bytes(4, "little"), 1)
        assert result is not None
        assert result.hash == tx2.hash

    def test_on_persist_stores_transactions_retrievable_by_hash(self):
        ledger = LedgerContract()
        snapshot = _Snapshot()

        tx1 = _tx(10, 0xAA)
        tx2 = _tx(20, 0xBB)
        block = _block_with_transactions(index=88, txs=[tx1, tx2])
        engine = _Engine(snapshot=snapshot, persisting_block=block)

        ledger.on_persist(engine)

        result = ledger.get_transaction(engine, tx1.hash)
        assert result is not None
        assert result.hash == tx1.hash
