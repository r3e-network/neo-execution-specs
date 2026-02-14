"""Map stack item."""

from __future__ import annotations
from typing import Dict, Iterator, TYPE_CHECKING
from neo.vm.types.stack_item import StackItem, StackItemType

if TYPE_CHECKING:
    from neo.vm.reference_counter import ReferenceCounter


class Map(StackItem):
    """Key-value map on the stack."""
    
    __slots__ = ("_items", "_reference_counter")
    
    def __init__(self, reference_counter: ReferenceCounter | None = None) -> None:
        self._items: Dict[StackItem, StackItem] = {}
        self._reference_counter = reference_counter

    def _ref_add(self, item: StackItem) -> None:
        if self._reference_counter is not None:
            self._reference_counter.add_reference(item)

    def _ref_remove(self, item: StackItem) -> None:
        if self._reference_counter is not None:
            self._reference_counter.remove_reference(item)
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.MAP
    
    def get_boolean(self) -> bool:
        return True
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __getitem__(self, key: StackItem) -> StackItem:
        return self._items[key]
    
    def __setitem__(self, key: StackItem, value: StackItem) -> None:
        if key in self._items:
            old_value = self._items[key]
            self._ref_remove(old_value)
        else:
            self._ref_add(key)
        self._items[key] = value
        self._ref_add(value)
    
    def __contains__(self, key: StackItem) -> bool:
        return key in self._items
    
    def keys(self) -> Iterator[StackItem]:
        return iter(self._items.keys())
    
    def values(self) -> Iterator[StackItem]:
        return iter(self._items.values())
    
    def items(self):
        """Return iterator over key-value pairs."""
        return self._items.items()
    
    def __delitem__(self, key: StackItem) -> None:
        value = self._items[key]
        del self._items[key]
        self._ref_remove(key)
        self._ref_remove(value)
    
    def clear(self) -> None:
        """Clear all items."""
        for key, value in self._items.items():
            self._ref_remove(key)
            self._ref_remove(value)
        self._items.clear()
