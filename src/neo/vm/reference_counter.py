"""Reference counter for preventing circular reference DoS attacks."""

from __future__ import annotations
from typing import Dict, Set, TYPE_CHECKING
from weakref import WeakSet

if TYPE_CHECKING:
    from neo.vm.types.stack_item import StackItem


class ReferenceCounter:
    """
    Tracks references between compound types to prevent circular reference attacks.
    
    When a compound type (Array, Struct, Map) references another item,
    the reference is tracked. Items with zero references can be collected.
    """
    
    def __init__(self) -> None:
        self._references: Dict[int, int] = {}  # item_id -> ref_count
        self._zero_referred: Set[int] = set()
        self._count: int = 0
    
    @property
    def count(self) -> int:
        """Total tracked items."""
        return self._count
    
    def add_reference(self, item: StackItem) -> None:
        """Add a reference to an item."""
        item_id = id(item)
        if item_id in self._references:
            self._references[item_id] += 1
            self._zero_referred.discard(item_id)
        else:
            self._references[item_id] = 1
            self._count += 1
    
    def remove_reference(self, item: StackItem) -> None:
        """Remove a reference from an item."""
        item_id = id(item)
        if item_id not in self._references:
            return
        
        self._references[item_id] -= 1
        if self._references[item_id] == 0:
            self._zero_referred.add(item_id)
    
    def check_zero_referred(self) -> int:
        """Get count of items with zero references."""
        return len(self._zero_referred)
