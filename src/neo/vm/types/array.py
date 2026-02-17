"""Array stack item."""

from __future__ import annotations
from collections.abc import Iterator
from typing import TYPE_CHECKING
from neo.vm.types.stack_item import StackItem, StackItemType

if TYPE_CHECKING:
    from neo.vm.reference_counter import ReferenceCounter

class Array(StackItem):
    """Mutable array on the stack."""
    
    __slots__ = ("_items", "_reference_counter")
    
    def __init__(
        self,
        reference_counter: ReferenceCounter | None = None,
        items: list[StackItem] | None = None
    ) -> None:
        self._reference_counter = reference_counter
        self._items: list[StackItem] = items if items is not None else []
        for item in self._items:
            self._ref_add(item)

    def _ref_add(self, item: StackItem) -> None:
        if self._reference_counter is not None:
            self._reference_counter.add_reference(item)

    def _ref_remove(self, item: StackItem) -> None:
        if self._reference_counter is not None:
            self._reference_counter.remove_reference(item)
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.ARRAY
    
    def get_boolean(self) -> bool:
        return True
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __getitem__(self, index: int) -> StackItem:
        return self._items[index]
    
    def __setitem__(self, index: int, value: StackItem) -> None:
        old = self._items[index]
        self._ref_remove(old)
        self._items[index] = value
        self._ref_add(value)
    
    def __iter__(self) -> Iterator[StackItem]:
        return iter(self._items)
    
    def append(self, item: StackItem) -> None:
        self._items.append(item)
        self._ref_add(item)

    def add(self, item: StackItem) -> None:
        """Alias for append."""
        self._items.append(item)
        self._ref_add(item)

    def remove_at(self, index: int) -> None:
        """Remove item at index."""
        item = self._items[index]
        del self._items[index]
        self._ref_remove(item)
    
    def reverse(self) -> None:
        """Reverse items in place."""
        self._items.reverse()
    
    def clear(self) -> None:
        for item in self._items:
            self._ref_remove(item)
        self._items.clear()
