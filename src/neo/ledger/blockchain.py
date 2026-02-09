"""
Blockchain - Blockchain state management.

Reference: Neo.Ledger.Blockchain
"""

from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from neo.types.uint256 import UInt256

if TYPE_CHECKING:
    from neo.network.payloads.block import Block
    from neo.persistence.store import IStore


@dataclass
class ApplicationExecuted:
    """Result of smart contract execution."""
    
    tx_hash: Optional[UInt256] = None
    trigger: str = "Application"
    vm_state: str = "HALT"
    gas_consumed: int = 0
    exception: Optional[str] = None
    stack: List = field(default_factory=list)
    notifications: List = field(default_factory=list)


class Blockchain:
    """Manages blockchain state and block persistence."""
    
    def __init__(self, store: "IStore") -> None:
        self._store = store
        self._lock = RLock()
        self._block_cache: Dict[UInt256, "Block"] = {}
        self._current_block: Optional["Block"] = None
        self._genesis_block: Optional["Block"] = None
        
        # Event callbacks
        self._on_persist: List[Callable[["Block"], None]] = []
        self._on_committed: List[Callable[["Block"], None]] = []
    
    @property
    def height(self) -> int:
        """Current blockchain height."""
        with self._lock:
            if self._current_block is None:
                return -1
            return self._current_block.index
    
    @property
    def current_block(self) -> Optional["Block"]:
        """Get current block."""
        with self._lock:
            return self._current_block
    
    @property
    def genesis_block(self) -> Optional["Block"]:
        """Get genesis block."""
        with self._lock:
            return self._genesis_block
    
    def get_block(self, block_hash: UInt256) -> Optional["Block"]:
        """Get block by hash."""
        with self._lock:
            return self._block_cache.get(block_hash)
    
    def get_block_by_index(self, index: int) -> Optional["Block"]:
        """Get block by index."""
        with self._lock:
            for block in self._block_cache.values():
                if block.index == index:
                    return block
            return None
    
    def contains_block(self, block_hash: UInt256) -> bool:
        """Check if block exists."""
        with self._lock:
            return block_hash in self._block_cache
    
    def persist(self, block: "Block") -> List[ApplicationExecuted]:
        """Persist a block to the blockchain."""
        with self._lock:
            results: List[ApplicationExecuted] = []
            
            # Cache the block
            self._block_cache[block.hash] = block
            
            # Update current block
            self._current_block = block
            
            # Set genesis if first block
            if block.index == 0:
                self._genesis_block = block
            
            # Fire persist callbacks
            for callback in self._on_persist:
                callback(block)
            
            return results
    
    def on_persist(self, callback: Callable[["Block"], None]) -> None:
        """Register persist callback."""
        self._on_persist.append(callback)
    
    def on_committed(self, callback: Callable[["Block"], None]) -> None:
        """Register committed callback."""
        self._on_committed.append(callback)
