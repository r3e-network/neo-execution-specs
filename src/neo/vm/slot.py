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
        items: Optional[List[StackItem]] = None,
        reference_counter: Optional[ReferenceCounter] = None
    ) -> None:
        self._items: List[StackItem] = items or []
        self._reference_counter = reference_counter
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __getitem__(self, index: int) -> StackItem:
        return self._items[index]
    
    def __setitem__(self, index: int, value: StackItem) -> None:
        old_value = self._items[index]
        self._items[index] = value
