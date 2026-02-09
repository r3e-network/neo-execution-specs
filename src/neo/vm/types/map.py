"""Map stack item."""

from __future__ import annotations
from typing import Dict, Iterator, TYPE_CHECKING
from neo.vm.types.stack_item import StackItem, StackItemType

if TYPE_CHECKING:
    pass


class Map(StackItem):
    """Key-value map on the stack."""
    
    __slots__ = ("_items", "_reference_counter")
    
    def __init__(self, reference_counter=None) -> None:
        self._items: Dict[StackItem, StackItem] = {}
        self._reference_counter = reference_counter
    
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
        self._items[key] = value
    
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
        del self._items[key]
    
    def clear(self) -> None:
        """Clear all items."""
        self._items.clear()
