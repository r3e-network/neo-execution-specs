"""Array stack item."""

from __future__ import annotations
from typing import List, Iterator, TYPE_CHECKING
from neo.vm.types.stack_item import StackItem, StackItemType

if TYPE_CHECKING:
    from neo.vm.reference_counter import ReferenceCounter


class Array(StackItem):
    """Mutable array on the stack."""
    
    __slots__ = ("_items", "_reference_counter")
    
    def __init__(
        self, 
        reference_counter: ReferenceCounter | None = None,
        items: List[StackItem] | None = None
    ) -> None:
        self._reference_counter = reference_counter
        self._items: List[StackItem] = items if items is not None else []
    
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
        self._items[index] = value
    
    def __iter__(self) -> Iterator[StackItem]:
        return iter(self._items)
    
    def append(self, item: StackItem) -> None:
        self._items.append(item)
    
    def add(self, item: StackItem) -> None:
        """Alias for append."""
        self._items.append(item)
    
    def remove_at(self, index: int) -> None:
        """Remove item at index."""
        del self._items[index]
    
    def reverse(self) -> None:
        """Reverse items in place."""
        self._items.reverse()
    
    def clear(self) -> None:
        self._items.clear()
