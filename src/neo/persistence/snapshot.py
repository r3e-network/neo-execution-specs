"""Neo N3 Snapshot - Database snapshot for atomic operations.

Reference: Neo.Persistence.Snapshot
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterator, Optional, Tuple, Any
from abc import ABC, abstractmethod

from neo.persistence.store import IStore


class Snapshot(ABC):
    """Abstract database snapshot for atomic operations.
    
    A snapshot provides isolated read/write access to the database,
    with changes only visible after commit.
    """
    
    @abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        """Get value by key."""
        pass
    
    @abstractmethod
    def contains(self, key: bytes) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    def put(self, key: bytes, value: bytes) -> None:
        """Put key-value pair."""
        pass
    
    @abstractmethod
    def delete(self, key: bytes) -> None:
        """Delete key."""
        pass
    
    @abstractmethod
    def find(self, prefix: bytes) -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with prefix."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit changes."""
        pass

    def try_get(self, key: bytes) -> Optional[bytes]:
        """Try to get a value by key. Returns None if not found."""
        return self.get(key)

    def get_and_change(self, key: bytes, factory: Optional[Callable[[], bytes]] = None) -> Optional[bytes]:
        """Get value and mark for change."""
        value = self.get(key)
        if value is None and factory is not None:
            value = factory()
            self.put(key, value)
        return value
    
    def add(self, key: bytes, value: bytes) -> None:
        """Add new key-value pair (raises if exists)."""
        if self.contains(key):
            raise KeyError(f"Key already exists: {key.hex()}")
        self.put(key, value)


    # Storage helper methods for ApplicationEngine
    def storage_get(self, key: bytes) -> Optional[bytes]:
        """Get storage value by key."""
        return self.get(key)

    def storage_put(self, key: bytes, value: bytes) -> None:
        """Set storage value."""
        self.put(key, value)

    def storage_delete(self, key: bytes) -> None:
        """Delete storage value."""
        self.delete(key)

    # Contract/ledger helper methods
    def get_contract(self, script_hash: Any) -> Optional[Any]:
        """Get contract data by script hash."""
        return None

    def contains_transaction(self, tx_hash: Any) -> bool:
        """Check whether a transaction exists."""
        return False

    def get_gas_balance(self, account: Any) -> int:
        """Get GAS balance for account."""
        return 0

@dataclass
class MemorySnapshot(Snapshot):
    """In-memory snapshot implementation."""
    
    _store: Dict[bytes, bytes] = field(default_factory=dict)
    _changes: Dict[bytes, Optional[bytes]] = field(default_factory=dict)
    
    def get(self, key: bytes) -> Optional[bytes]:
        if key in self._changes:
            return self._changes[key]
        return self._store.get(key)
    
    def contains(self, key: bytes) -> bool:
        if key in self._changes:
            return self._changes[key] is not None
        return key in self._store
    
    def put(self, key: bytes, value: bytes) -> None:
        self._changes[key] = value
    
    def delete(self, key: bytes) -> None:
        self._changes[key] = None
    
    def find(self, prefix: bytes) -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with prefix, sorted by key."""
        seen = set()
        results: Dict[bytes, bytes] = {}
        # Collect from changes (overrides store)
        for key, value in self._changes.items():
            if key.startswith(prefix):
                seen.add(key)
                if value is not None:
                    results[key] = value
        # Collect from store (excluding changed keys)
        for key, value in self._store.items():
            if key.startswith(prefix) and key not in seen:
                results[key] = value
        # Yield sorted for deterministic ordering
        for key in sorted(results):
            yield key, results[key]

    def commit(self) -> None:
        for key, value in self._changes.items():
            if value is None:
                self._store.pop(key, None)
            else:
                self._store[key] = value
        self._changes.clear()
    
    def clone(self) -> "MemorySnapshot":
        """Create a clone of this snapshot."""
        clone = MemorySnapshot()
        clone._store = dict(self._store)
        clone._changes = dict(self._changes)
        return clone
    
    # Storage helper methods for ApplicationEngine
    def storage_get(self, key: bytes) -> Optional[bytes]:
        """Get storage value."""
        return self.get(key)
    
    def storage_put(self, key: bytes, value: bytes) -> None:
        """Put storage value."""
        self.put(key, value)
    
    def storage_delete(self, key: bytes) -> None:
        """Delete storage value."""
        self.delete(key)
    
    # Contract methods
    def get_contract(self, script_hash) -> Optional[Any]:
        """Get contract by script hash."""
        from neo.types.uint160 import UInt160
        if isinstance(script_hash, UInt160):
            key = b"\x08" + bytes(script_hash)  # Contract prefix
        else:
            key = b"\x08" + script_hash
        return self.get(key)
    
    def contains_transaction(self, tx_hash) -> bool:
        """Check if transaction exists."""
        from neo.types.uint256 import UInt256
        if isinstance(tx_hash, UInt256):
            key = b"\x0b" + bytes(tx_hash)  # Transaction prefix
        else:
            key = b"\x0b" + tx_hash
        return self.contains(key)
    
    def get_gas_balance(self, account) -> int:
        """Get GAS balance for account."""
        from neo.types.uint160 import UInt160
        if isinstance(account, UInt160):
            key = b"\x14\x00" + bytes(account)  # GAS balance prefix
        else:
            key = b"\x14\x00" + account
        value = self.get(key)
        if value is None:
            return 0
        return int.from_bytes(value, 'little')


class StoreSnapshot(Snapshot):
    """Snapshot backed by an IStore."""
    
    def __init__(self, store: IStore):
        self._store = store
        self._changes: Dict[bytes, Optional[bytes]] = {}
    
    def get(self, key: bytes) -> Optional[bytes]:
        if key in self._changes:
            return self._changes[key]
        return self._store.get(key)
    
    def contains(self, key: bytes) -> bool:
        if key in self._changes:
            return self._changes[key] is not None
        return self._store.contains(key)
    
    def put(self, key: bytes, value: bytes) -> None:
        self._changes[key] = value
    
    def delete(self, key: bytes) -> None:
        self._changes[key] = None
    
    def find(self, prefix: bytes) -> Iterator[Tuple[bytes, bytes]]:
        """Find all key-value pairs with prefix, sorted by key."""
        seen = set()
        results: Dict[bytes, bytes] = {}
        # Collect from changes (overrides store)
        for key, value in self._changes.items():
            if key.startswith(prefix):
                seen.add(key)
                if value is not None:
                    results[key] = value
        # Collect from store (excluding changed keys)
        for key, value in self._store.seek(prefix, 1):
            if key not in seen:
                results[key] = value
        # Yield sorted for deterministic ordering
        for key in sorted(results):
            yield key, results[key]
    
    def commit(self) -> None:
        for key, value in self._changes.items():
            if value is None:
                self._store.delete(key)
            else:
                self._store.put(key, value)
        self._changes.clear()
