"""Boolean stack item."""

from __future__ import annotations
from neo.vm.types.stack_item import StackItem, StackItemType


class Boolean(StackItem):
    """Boolean value on the stack."""
    
    TRUE: Boolean
    FALSE: Boolean
    
    __slots__ = ("_value",)
    
    def __init__(self, value: bool) -> None:
        self._value = value
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.BOOLEAN
    
    @property
    def value(self) -> bool:
        return self._value
    
    def get_boolean(self) -> bool:
        return self._value
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Boolean):
            return self._value == other._value
        return False
    
    def __hash__(self) -> int:
        return hash(self._value)


Boolean.TRUE = Boolean(True)
Boolean.FALSE = Boolean(False)
