"""Buffer stack item."""

from __future__ import annotations
from neo.vm.types.stack_item import StackItem, StackItemType
from neo.types import BigInteger


class Buffer(StackItem):
    """Mutable byte buffer on the stack."""
    
    __slots__ = ("_value",)
    
    def __init__(self, size_or_data: int | bytes = 0) -> None:
        if isinstance(size_or_data, int):
            self._value = bytearray(size_or_data)
        else:
            self._value = bytearray(size_or_data)
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.BUFFER
    
    @property
    def value(self) -> bytearray:
        return self._value
    
    def get_boolean(self) -> bool:
        return True
    
    def __len__(self) -> int:
        return len(self._value)
