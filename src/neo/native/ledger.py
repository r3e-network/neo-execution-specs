"""Ledger contract for blockchain data access."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, List

from neo.types import UInt256
from neo.native.native_contract import NativeContract, CallFlags, StorageItem
from neo.network.payloads.block import Block
from neo.network.payloads.transaction import Transaction


# Storage prefixes
PREFIX_BLOCK_HASH = 9
PREFIX_CURRENT_BLOCK = 12
PREFIX_BLOCK = 5
PREFIX_TRANSACTION = 11


@dataclass
class HashIndexState:
    """Current block hash and index."""
    hash: Optional[UInt256] = None
    index: int = 0
    
    def to_bytes(self) -> bytes:
        data = self.hash.data if self.hash else b'\x00' * 32
        data += self.index.to_bytes(4, 'little')
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'HashIndexState':
        state = cls()
        if data and len(data) >= 36:
            state.hash = UInt256(data[:32])
            state.index = int.from_bytes(data[32:36], 'little')
        return state


@dataclass
class TransactionState:
    """State of a transaction in storage."""
    block_index: int = 0
    transaction: Optional[Any] = None
    state: int = 0  # VMState: 0=NONE, 1=HALT, 2=FAULT
    
    def to_bytes(self) -> bytes:
        from neo.io.binary_writer import BinaryWriter

        writer = BinaryWriter()
        writer.write_uint32(self.block_index)
        writer.write_byte(self.state)
        writer.write_var_bytes(self._serialize_transaction(self.transaction))
        return writer.to_bytes()

    @staticmethod
    def _serialize_transaction(transaction: Optional[Any]) -> bytes:
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
    def from_bytes(cls, data: bytes) -> 'TransactionState':
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


class LedgerContract(NativeContract):
    """Provides access to blockchain data.
    
    Stores blocks and transactions, provides query methods.
    """
    
    def __init__(self) -> None:
        super().__init__()
    
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
    
    def get_block_hash(self, snapshot: Any, index: int) -> Optional[UInt256]:
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
    
    def get_transaction_state(self, snapshot: Any, hash: UInt256) -> Optional[TransactionState]:
        """Get transaction state by hash."""
        key = self._create_storage_key(PREFIX_TRANSACTION, hash.data)
        item = snapshot.get(key)
        if item is None:
            return None
        return TransactionState.from_bytes(item.value)
    
    def get_block(self, engine: Any, index_or_hash: bytes) -> Optional[Block]:
        """Get a block by index or hash."""
        if len(index_or_hash) < 32:
            index = int.from_bytes(index_or_hash, 'little')
            hash = self.get_block_hash(engine.snapshot, index)
        else:
            hash = UInt256(index_or_hash)
        
        if hash is None:
            return None
        
        key = self._create_storage_key(PREFIX_BLOCK, hash.data)
        item = engine.snapshot.get(key)
        return item.value if item else None
    
    def get_transaction(self, engine: Any, hash: UInt256) -> Optional[Transaction]:
        """Get a transaction by hash."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None:
            return None
        return state.transaction
    
    def get_transaction_height(self, engine: Any, hash: UInt256) -> int:
        """Get the block height of a transaction."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None:
            return -1
        return state.block_index
    
    def get_transaction_signers(self, engine: Any, hash: UInt256) -> Optional[List[Any]]:
        """Get transaction signers."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None or state.transaction is None:
            return None
        return getattr(state.transaction, 'signers', [])
    
    def get_transaction_vm_state(self, engine: Any, hash: UInt256) -> int:
        """Get transaction VM state (0=NONE, 1=HALT, 2=FAULT)."""
        state = self.get_transaction_state(engine.snapshot, hash)
        if state is None:
            return 0  # NONE
        return state.state
    
    def get_transaction_from_block(
        self, engine: Any, block_index_or_hash: bytes, tx_index: int
    ) -> Optional[Transaction]:
        """Get a transaction from a block by index."""
        if tx_index < 0:
            return None

        if len(block_index_or_hash) < 32:
            index = int.from_bytes(block_index_or_hash, 'little')
            hash = self.get_block_hash(engine.snapshot, index)
        else:
            hash = UInt256(block_index_or_hash)
        
        if hash is None:
            return None
        
        # Get block and extract transaction
        block = self.get_block(engine, hash.data)
        if block is None:
            return None

        txs = self._extract_block_transactions(block)
        if txs is None or tx_index >= len(txs):
            return None
        return txs[tx_index]

    @staticmethod
    def _extract_block_transactions(block: Any) -> Optional[List[Any]]:
        txs = getattr(block, "transactions", None)
        if txs is not None:
            return list(txs)

        if isinstance(block, (bytes, bytearray)):
            from neo.io.binary_reader import BinaryReader
            from neo.network.payloads.block import Block

            try:
                reader = BinaryReader(bytes(block))
                parsed = Block.deserialize(reader)
                return list(parsed.transactions)
            except Exception:
                return None

        return None

    @staticmethod
    def _serialize_block(block: Any) -> bytes:
        if isinstance(block, (bytes, bytearray)):
            return bytes(block)

        to_bytes = getattr(block, "to_bytes", None)
        if callable(to_bytes):
            return bytes(to_bytes())

        serialize = getattr(block, "serialize", None)
        if callable(serialize):
            from neo.io.binary_writer import BinaryWriter

            writer = BinaryWriter()
            serialize(writer)
            return writer.to_bytes()

        raise TypeError("Block does not support byte serialization")
    
    def on_persist(self, engine: Any) -> None:
        """Store block and transactions when persisting."""
        block = engine.persisting_block
        block_hash = block.hash.data if hasattr(block.hash, "data") else bytes(block.hash)
        
        # Store block hash by index
        hash_key = self._create_storage_key(PREFIX_BLOCK_HASH, block.index)
        engine.snapshot.add(hash_key, StorageItem(block_hash))
        
        # Store block
        block_key = self._create_storage_key(PREFIX_BLOCK, block_hash)
        engine.snapshot.add(block_key, StorageItem(self._serialize_block(block)))
        
        # Store transactions
        for tx in block.transactions:
            tx_hash = tx.hash.data if hasattr(tx.hash, "data") else bytes(tx.hash)
            tx_state = TransactionState(
                block_index=block.index,
                transaction=tx,
                state=0  # NONE initially
            )
            tx_key = self._create_storage_key(PREFIX_TRANSACTION, tx_hash)
            engine.snapshot.add(tx_key, StorageItem(tx_state.to_bytes()))
    
    def post_persist(self, engine: Any) -> None:
        """Update current block after persisting."""
        block = engine.persisting_block
        
        key = self._create_storage_key(PREFIX_CURRENT_BLOCK)
        state = HashIndexState(hash=block.hash, index=block.index)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.value = state.to_bytes()
