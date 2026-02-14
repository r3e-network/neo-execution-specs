"""Slot for storing local variables, arguments, and static fields."""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from neo.vm.types.stack_item import StackItem
    from neo.vm.reference_counter import ReferenceCounter


class Slot:
    """
    Storage slot for variables.
    
    Used for:
    - Arguments (function parameters)
    - Local variables
    - Static fields
    """
    
    def __init__(
        self,
        count_or_items: int | List["StackItem"] | None = None,
        reference_counter: Optional["ReferenceCounter"] = None
    ) -> None:
        from neo.vm.types import NULL
        if isinstance(count_or_items, int):
            # Create slot with count NULL items
            self._items: List["StackItem"] = [NULL for _ in range(count_or_items)]
        elif count_or_items is None:
            self._items = []
        else:
            self._items = list(count_or_items)
        self._reference_counter = reference_counter
        for item in self._items:
            self._ref_add(item)

    def _ref_add(self, item: "StackItem") -> None:
        if self._reference_counter is not None:
            self._reference_counter.add_reference(item)

    def _ref_remove(self, item: "StackItem") -> None:
        if self._reference_counter is not None:
            self._reference_counter.remove_reference(item)
    
    @classmethod
    def from_items(cls, items: List["StackItem"], 
                   reference_counter: Optional["ReferenceCounter"] = None) -> "Slot":
        """Create slot from list of items."""
        return cls(items, reference_counter)
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __getitem__(self, index: int) -> StackItem:
        return self._items[index]
    
    def __setitem__(self, index: int, value: "StackItem") -> None:
        old = self._items[index]
        self._ref_remove(old)
        self._items[index] = value
        self._ref_add(value)
