"""Struct stack item."""

from __future__ import annotations
from neo.vm.types.array import Array
from neo.vm.types.stack_item import StackItemType


class Struct(Array):
    """Struct - similar to Array but with value semantics for cloning."""
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.STRUCT
    
    def clone(self) -> Struct:
        """Create a deep copy of this struct."""
        return Struct([item for item in self._items])
