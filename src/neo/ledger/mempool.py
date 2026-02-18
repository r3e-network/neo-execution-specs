"""
MemoryPool - Transaction memory pool.

Reference: Neo.Ledger.MemoryPool
"""

from __future__ import annotations

from collections.abc import Iterator
from threading import RLock
from typing import TYPE_CHECKING

from neo.ledger.pool_item import PoolItem
from neo.ledger.verify_result import VerifyResult
from neo.types.uint256 import UInt256

if TYPE_CHECKING:
    from neo.network.payloads.transaction import Transaction

class MemoryPool:
    """Cache for verified transactions before block inclusion."""
    
    DEFAULT_CAPACITY = 50_000
    
    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        self._capacity = capacity
        self._lock = RLock()
        
        # Verified transactions
        self._verified: dict[UInt256, PoolItem] = {}
        
        # Unverified transactions (valid in prior block)
        self._unverified: dict[UInt256, PoolItem] = {}
    
    @property
    def capacity(self) -> int:
        """Maximum pool capacity."""
        return self._capacity
    
    @property
    def count(self) -> int:
        """Total transaction count."""
        with self._lock:
            return len(self._verified) + len(self._unverified)
    
    @property
    def verified_count(self) -> int:
        """Verified transaction count."""
        with self._lock:
            return len(self._verified)
    
    @property
    def unverified_count(self) -> int:
        """Unverified transaction count."""
        with self._lock:
            return len(self._unverified)
    
    def contains_key(self, tx_hash: UInt256) -> bool:
        """Check if transaction exists in pool."""
        with self._lock:
            return tx_hash in self._verified or tx_hash in self._unverified
    
    def try_get(self, tx_hash: UInt256) -> Transaction | None:
        """Get transaction by hash."""
        with self._lock:
            if tx_hash in self._verified:
                return self._verified[tx_hash].tx
            if tx_hash in self._unverified:
                return self._unverified[tx_hash].tx
            return None
    
    def get_verified_transactions(self) -> list[Transaction]:
        """Get all verified transactions."""
        with self._lock:
            return [item.tx for item in self._verified.values()]
    
    def try_add(self, tx: Transaction) -> VerifyResult:
        """Try to add a transaction to the pool."""
        with self._lock:
            tx_hash = tx.hash
            
            # Check if already in pool
            if tx_hash in self._verified:
                return VerifyResult.ALREADY_IN_POOL
            if tx_hash in self._unverified:
                return VerifyResult.ALREADY_IN_POOL
            
            # Check capacity
            if len(self._verified) >= self._capacity:
                return VerifyResult.OUT_OF_MEMORY
            
            # Add to verified pool
            self._verified[tx_hash] = PoolItem(tx)
            return VerifyResult.SUCCEED
    
    def remove(self, tx_hash: UInt256) -> bool:
        """Remove a transaction from the pool."""
        with self._lock:
            if tx_hash in self._verified:
                del self._verified[tx_hash]
                return True
            if tx_hash in self._unverified:
                del self._unverified[tx_hash]
                return True
            return False
    
    def invalidate_verified_transactions(self) -> None:
        """Move all verified transactions to unverified."""
        with self._lock:
            self._unverified.update(self._verified)
            self._verified.clear()
    
    def clear(self) -> None:
        """Clear all transactions from the pool."""
        with self._lock:
            self._verified.clear()
            self._unverified.clear()
    
    def __iter__(self) -> Iterator[Transaction]:
        """Iterate over all transactions."""
        with self._lock:
            items = list(self._verified.values()) + list(self._unverified.values())
        for item in items:
            yield item.tx
    
    def __len__(self) -> int:
        """Get total count."""
        return self.count
    
    def __contains__(self, tx_hash: UInt256) -> bool:
        """Check if hash in pool."""
        return self.contains_key(tx_hash)
