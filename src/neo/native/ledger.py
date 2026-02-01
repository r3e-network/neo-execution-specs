"""Ledger contract for blockchain data access."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, List

from neo.types import UInt160, UInt256
from neo.native.native_contract import NativeContract, CallFlags, StorageItem


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


class LedgerContract(NativeContract):
    """Provides access to blockchain data."""
    
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
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransaction", self.get_transaction,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransactionHeight", self.get_transaction_height,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransactionSigners", self.get_transaction_signers,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getTransactionVMState", self.get_transaction_vm_state,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
    
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
    
    def get_block(self, engine: Any, index_or_hash: bytes) -> Optional[Any]:
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
    
    def get_transaction(self, engine: Any, hash: UInt256) -> Optional[Any]:
        """Get a transaction by hash."""
        key = self._create_storage_key(PREFIX_TRANSACTION, hash.data)
        item = engine.snapshot.get(key)
        return item.value if item else None
    
    def get_transaction_height(self, engine: Any, hash: UInt256) -> int:
        """Get the block height of a transaction."""
        key = self._create_storage_key(PREFIX_TRANSACTION, hash.data)
        item = engine.snapshot.get(key)
        if item is None:
            return -1
        # Parse block index from transaction state
        return int.from_bytes(item.value[:4], 'little') if item.value else -1
    
    def get_transaction_signers(self, engine: Any, hash: UInt256) -> Optional[List[Any]]:
        """Get transaction signers."""
        key = self._create_storage_key(PREFIX_TRANSACTION, hash.data)
        item = engine.snapshot.get(key)
        if item is None:
            return None
        # In real impl, would parse signers from transaction
        return []
    
    def get_transaction_vm_state(self, engine: Any, hash: UInt256) -> int:
        """Get transaction VM state."""
        key = self._create_storage_key(PREFIX_TRANSACTION, hash.data)
        item = engine.snapshot.get(key)
        if item is None:
            return 0  # NONE
        # In real impl, would parse VM state from transaction state
        return 1  # HALT
