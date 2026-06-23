"""Ledger contract for blockchain data access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neo.hardfork import Hardfork
from neo.native.native_contract import CallFlags, NativeContract, StorageItem
from neo.network.payloads.transaction import (
    Transaction,
)
from neo.network.payloads.transaction_attribute import TransactionAttributeType
from neo.types import UInt256

# Default MaxTraceableBlocks protocol setting (mainnet), used as a fallback
# when no protocol settings are available on the engine (e.g. lightweight
# unit-test stubs). Mirrors ProtocolSettings.MaxTraceableBlocks.
DEFAULT_MAX_TRACEABLE_BLOCKS = 2_102_400

# Storage prefixes
PREFIX_BLOCK_HASH = 9
PREFIX_CURRENT_BLOCK = 12
PREFIX_BLOCK = 5
PREFIX_TRANSACTION = 11

@dataclass
class HashIndexState:
    """Current block hash and index."""

    hash: UInt256 | None = None
    index: int = 0
    
    def to_bytes(self) -> bytes:
        data = self.hash.data if self.hash else b'\x00' * 32
        data += self.index.to_bytes(4, 'little')
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> HashIndexState:
        state = cls()
        if data and len(data) >= 36:
            state.hash = UInt256(data[:32])
            state.index = int.from_bytes(data[32:36], 'little')
        return state

@dataclass
class TransactionState:
    """State of a transaction in storage."""

    block_index: int = 0
    transaction: Any | None = None
    state: int = 0  # VMState: 0=NONE, 1=HALT, 2=FAULT
    
    def to_bytes(self) -> bytes:
        from neo.io.binary_writer import BinaryWriter

        writer = BinaryWriter()
        writer.write_uint32(self.block_index)
        writer.write_byte(self.state)
        writer.write_var_bytes(self._serialize_transaction(self.transaction))
        return writer.to_bytes()

    @staticmethod
    def _serialize_transaction(transaction: Any | None) -> bytes:
        if transaction is None:
            return b""
        if isinstance(transaction, (bytes, bytearray)):
            return bytes(transaction)
        to_bytes = getattr(transaction, "to_bytes", None)
        if callable(to_bytes):
            return bytes(to_bytes())
        serialize = getattr(transaction, "serialize", None)
        if callable(serialize):
            from neo.io.binary_writer import BinaryWriter

            writer = BinaryWriter()
            serialize(writer)
            return writer.to_bytes()
        return b""
    
    @classmethod
    def from_bytes(cls, data: bytes) -> TransactionState:
        state = cls()
        if data and len(data) >= 4:
            state.block_index = int.from_bytes(data[:4], 'little')
            if len(data) > 4:
                state.state = data[4]
            if len(data) > 5:
                from neo.io.binary_reader import BinaryReader
                from neo.network.payloads.transaction import Transaction

                try:
                    reader = BinaryReader(data[5:])
                    tx_bytes = reader.read_var_bytes(max_length=len(data) - 5)
                except Exception:
                    # Backwards compatibility with older storage format.
                    tx_bytes = b""
                if tx_bytes:
                    try:
                        tx_reader = BinaryReader(tx_bytes)
                        state.transaction = Transaction.deserialize(tx_reader)
                    except Exception:
                        state.transaction = tx_bytes
        return state

@dataclass
class TrimmedBlock:
    """A block whose transactions are trimmed down to their hashes.

    Mirrors C# Neo.SmartContract.Native.TrimmedBlock: the serialized form is the
    block header followed by a var-length array of 32-byte transaction hashes.
    This is the value stored under Prefix_Block (state-root critical).
    """

    header: Any = None
    hashes: list[bytes] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.hashes is None:
            self.hashes = []

    @property
    def index(self) -> int:
        return int(getattr(self.header, "index", 0))

    @classmethod
    def create(cls, block: Any) -> "TrimmedBlock":
        from neo.network.payloads.header import Header

        header = Header(
            version=block.version,
            prev_hash=block.prev_hash,
            merkle_root=block.merkle_root,
            timestamp=block.timestamp,
            nonce=block.nonce,
            index=block.index,
            primary_index=block.primary_index,
            next_consensus=block.next_consensus,
            witness=block.witness,
        )
        hashes = []
        for tx in getattr(block, "transactions", []):
            tx_hash = tx.hash.data if hasattr(tx.hash, "data") else bytes(tx.hash)
            hashes.append(bytes(tx_hash))
        return cls(header=header, hashes=hashes)

    def to_bytes(self) -> bytes:
        from neo.io.binary_writer import BinaryWriter

        writer = BinaryWriter()
        self.header.serialize(writer)
        writer.write_var_int(len(self.hashes))
        for h in self.hashes:
            writer.write_bytes(h)
        return writer.to_bytes()

    @classmethod
    def from_bytes(cls, data: bytes) -> "TrimmedBlock":
        from neo.io.binary_reader import BinaryReader
        from neo.network.payloads.header import Header

        reader = BinaryReader(bytes(data))
        header = Header.deserialize(reader)
        count = reader.read_var_int(0xFFFF)
        hashes = [reader.read_bytes(32) for _ in range(count)]
        return cls(header=header, hashes=hashes)


class LedgerContract(NativeContract):
    """Provides access to blockchain data.
    
    Stores blocks and transactions, provides query methods.
    """
    
    @property
    def name(self) -> str:
        return "LedgerContract"
    
    def _register_methods(self) -> None:
        """Register ledger methods."""
        super()._register_methods()
        self._register_method("currentHash", self.current_hash,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("currentIndex", self.current_index,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getBlock", self.get_block,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES,
                            manifest_parameter_names=["indexOrHash"])
        self._register_method("getTransaction", self.get_transaction,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransactionHeight", self.get_transaction_height,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransactionSigners", self.get_transaction_signers,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransactionVMState", self.get_transaction_vm_state,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransactionFromBlock", self.get_transaction_from_block,
                            cpu_fee=1 << 16, call_flags=CallFlags.READ_STATES,
                            manifest_parameter_names=["blockIndexOrHash", "txIndex"])
    
    def current_hash(self, snapshot: Any) -> UInt256:
        """Get the hash of the current block."""
        key = self._create_storage_key(PREFIX_CURRENT_BLOCK)
        item = snapshot.get(key)
        if item is None:
            return UInt256.ZERO
        state = HashIndexState.from_bytes(item.value)
        return state.hash or UInt256.ZERO
    
    def current_index(self, snapshot: Any) -> int:
        """Get the index of the current block."""
        key = self._create_storage_key(PREFIX_CURRENT_BLOCK)
        item = snapshot.get(key)
        if item is None:
            return 0
        state = HashIndexState.from_bytes(item.value)
        return state.index
    
    def get_block_hash(self, snapshot: Any, index: int) -> UInt256 | None:
        """Get block hash by index."""
        key = self._create_storage_key(PREFIX_BLOCK_HASH, index)
        item = snapshot.get(key)
        if item is None:
            return None
        return UInt256(item.value)
    
    def contains_block(self, snapshot: Any, hash: UInt256) -> bool:
        """Check if a block exists."""
        key = self._create_storage_key(PREFIX_BLOCK, hash.data)
        return snapshot.contains(key)
    
    def contains_transaction(self, snapshot: Any, hash: UInt256) -> bool:
        """Check if a transaction exists."""
        state = self.get_transaction_state(snapshot, hash)
        return state is not None and state.transaction is not None
    
    def get_transaction_state(self, snapshot: Any, hash: UInt256) -> TransactionState | None:
        """Get transaction state by hash.

        Mirrors C# LedgerContract.GetTransactionState (LedgerContract.cs:332-333):
        a stored state whose Transaction is null is a conflict stub and is hidden
        (returned as None), so it never leaks through get_transaction,
        get_transaction_height, get_transaction_vm_state or get_transaction_signers.
        """
        key = self._create_storage_key(PREFIX_TRANSACTION, hash.data)
        item = snapshot.get(key)
        if item is None:
            return None
        state = TransactionState.from_bytes(item.value)
        return state if state.transaction is not None else None
    
    def _max_traceable_blocks(self, engine: Any) -> int:
        """Resolve the MaxTraceableBlocks value for the current engine state.

        Mirrors C# LedgerContract.IsTraceableBlock(engine, index): the value comes
        from ProtocolSettings.MaxTraceableBlocks, but once HF_Echidna is active it is
        read from the native Policy contract instead (LedgerContract.cs:104-106).
        Falls back to DEFAULT_MAX_TRACEABLE_BLOCKS when no protocol settings are
        available (lightweight test stubs).
        """
        if NativeContract.is_hardfork_enabled(engine, Hardfork.HF_ECHIDNA):
            policy = self.get_contract_by_name("PolicyContract")
            if policy is not None:
                return policy.get_max_traceable_blocks(engine.snapshot)
        settings = getattr(engine, "protocol_settings", None)
        if settings is None:
            snapshot = getattr(engine, "snapshot", None)
            settings = getattr(snapshot, "protocol_settings", None)
        if settings is not None:
            value = getattr(settings, "max_traceable_blocks", None)
            if value is not None:
                return int(value)
        return DEFAULT_MAX_TRACEABLE_BLOCKS

    def _is_traceable_block(self, engine: Any, index: int) -> bool:
        """Whether a block at ``index`` is reachable from a smart contract.

        Mirrors C# LedgerContract.IsTraceableBlock (LedgerContract.cs:102-128):
        the block must not be in the future and must be within MaxTraceableBlocks
        of the current chain height.
        """
        current_index = self.current_index(engine.snapshot)
        if index > current_index:
            return False
        return index + self._max_traceable_blocks(engine) > current_index

    def get_trimmed_block(self, snapshot: Any, hash: UInt256) -> TrimmedBlock | None:
        """Read the stored TrimmedBlock for a block hash (no traceability gate).

        Mirrors C# LedgerContract.GetTrimmedBlock (LedgerContract.cs:240-248).
        """
        key = self._create_storage_key(PREFIX_BLOCK, hash.data)
        item = snapshot.get(key)
        if item is None:
            return None
        return TrimmedBlock.from_bytes(item.value)

    def get_block(self, engine: Any, index_or_hash: bytes) -> TrimmedBlock | None:
        """Get a block by index or hash.

        Mirrors C# LedgerContract.GetBlock (the contract-callable overload,
        LedgerContract.cs:251-265): resolves the hash, reads the TrimmedBlock and
        returns it only when its block index is traceable.
        """
        if len(index_or_hash) < 32:
            index = int.from_bytes(index_or_hash, 'little')
            hash = self.get_block_hash(engine.snapshot, index)
        else:
            hash = UInt256(index_or_hash)

        if hash is None:
            return None

        block = self.get_trimmed_block(engine.snapshot, hash)
        if block is None or not self._is_traceable_block(engine, block.index):
            return None
        return block
    
    def get_transaction(self, engine: Any, hash: UInt256) -> Transaction | None:
        """Get a transaction by hash."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None or not self._is_traceable_block(engine, state.block_index):
            return None
        return state.transaction

    def get_transaction_height(self, engine: Any, hash: UInt256) -> int:
        """Get the block height of a transaction."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None or not self._is_traceable_block(engine, state.block_index):
            return -1
        return state.block_index

    def get_transaction_signers(self, engine: Any, hash: UInt256) -> list[Any] | None:
        """Get transaction signers."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None or not self._is_traceable_block(engine, state.block_index):
            return None
        return getattr(state.transaction, 'signers', [])

    def get_transaction_vm_state(self, engine: Any, hash: UInt256) -> int:
        """Get transaction VM state (0=NONE, 1=HALT, 2=FAULT)."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None or not self._is_traceable_block(engine, state.block_index):
            return 0  # NONE
        return state.state
    
    def get_transaction_from_block(
        self, engine: Any, block_index_or_hash: bytes, tx_index: int
    ) -> Transaction | None:
        """Get a transaction from a block by index.

        Mirrors C# LedgerContract.GetTransactionFromBlock (LedgerContract.cs:382-394):
        an out-of-range txIndex (negative or >= the block's transaction count) raises
        an ArgumentOutOfRangeException (mapped to a VM FAULT) rather than returning
        null, and the resolved block must be traceable.
        """
        if len(block_index_or_hash) < 32:
            index = int.from_bytes(block_index_or_hash, 'little')
            hash = self.get_block_hash(engine.snapshot, index)
        else:
            hash = UInt256(block_index_or_hash)

        if hash is None:
            return None

        # Resolve the TrimmedBlock, then mirror C#'s exact ordering: traceability
        # check, out-of-range fault on txIndex, then resolve the tx by its hash.
        block = self.get_trimmed_block(engine.snapshot, hash)
        if block is None or not self._is_traceable_block(engine, block.index):
            return None

        if tx_index < 0 or tx_index >= len(block.hashes):
            raise ValueError(f"txIndex out of range: {tx_index}")

        tx_hash = UInt256(block.hashes[tx_index])
        state = self.get_transaction_state(engine.snapshot, tx_hash)
        return state.transaction if state is not None else None

    @staticmethod
    def _attribute_hash_bytes(attr: Any) -> bytes | None:
        """Extract the 32-byte conflict hash from a Conflicts attribute."""
        hash_value = getattr(attr, "hash", None)
        if hash_value is None:
            return None
        if hasattr(hash_value, "data"):
            return bytes(hash_value.data)
        return bytes(hash_value)

    def on_persist(self, engine: Any) -> None:
        """Store block and transactions when persisting."""
        block = engine.persisting_block
        block_hash = block.hash.data if hasattr(block.hash, "data") else bytes(block.hash)
        
        # Store block hash by index
        hash_key = self._create_storage_key(PREFIX_BLOCK_HASH, block.index)
        engine.snapshot.add(hash_key, StorageItem(block_hash))
        
        # Store the block as a TrimmedBlock (header + transaction hashes), matching
        # C# LedgerContract.OnPersistAsync (LedgerContract.cs:51). The full
        # transactions are stored separately under Prefix_Transaction below.
        block_key = self._create_storage_key(PREFIX_BLOCK, block_hash)
        engine.snapshot.add(block_key, StorageItem(TrimmedBlock.create(block).to_bytes()))
        
        # Store transactions
        for tx in block.transactions:
            tx_hash = tx.hash.data if hasattr(tx.hash, "data") else bytes(tx.hash)
            tx_state = TransactionState(
                block_index=block.index,
                transaction=tx,
                state=0  # NONE initially
            )
            # It's possible that there are previously saved malicious conflict
            # records for this transaction. Overwrite them with the real tx state
            # (mirrors C# GetAndChange(...).FromReplica(...), LedgerContract.cs:55-57).
            tx_key = self._create_storage_key(PREFIX_TRANSACTION, tx_hash)
            real_item = engine.snapshot.get_and_change(tx_key, lambda: StorageItem())
            real_item.value = tx_state.to_bytes()

            # Store the transaction's Conflicts records as dummy stubs so that a
            # later transaction conflicting with this hash is rejected. The stub's
            # transaction is None so contains_transaction / get_transaction* keep
            # treating the hash as absent (mirrors C# LedgerContract.cs:59-70).
            conflicting_signers = [
                signer.account for signer in getattr(tx, "signers", [])
            ]
            for attr in getattr(tx, "attributes", []):
                if int(getattr(attr, "type", -1)) != int(TransactionAttributeType.CONFLICTS):
                    continue
                attr_hash = self._attribute_hash_bytes(attr)
                if attr_hash is None:
                    continue
                stub = TransactionState(block_index=block.index, transaction=None)
                stub_bytes = stub.to_bytes()

                conflict_key = self._create_storage_key(PREFIX_TRANSACTION, attr_hash)
                conflict_item = engine.snapshot.get_and_change(conflict_key, lambda: StorageItem())
                conflict_item.value = stub_bytes

                for account in conflicting_signers:
                    account_bytes = account.data if hasattr(account, "data") else bytes(account)
                    signer_key = self._create_storage_key(
                        PREFIX_TRANSACTION, attr_hash, account_bytes
                    )
                    signer_item = engine.snapshot.get_and_change(
                        signer_key, lambda: StorageItem()
                    )
                    signer_item.value = stub_bytes
    
    def post_persist(self, engine: Any) -> None:
        """Update current block after persisting."""
        block = engine.persisting_block
        
        key = self._create_storage_key(PREFIX_CURRENT_BLOCK)
        state = HashIndexState(hash=block.hash, index=block.index)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.value = state.to_bytes()
