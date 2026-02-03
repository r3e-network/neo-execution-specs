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
    
    def get_span(self) -> bytes:
        """Get the raw bytes."""
        return bytes(self._value)
    
    def get_string(self) -> str:
        """Get as UTF-8 string."""
        return self._value.decode('utf-8', errors='replace')
    
    @property
    def inner_buffer(self) -> bytearray:
        """Get the mutable inner buffer."""
        return self._value
    
    def __len__(self) -> int:
        return len(self._value)
    
    def __setitem__(self, index: int, value: int) -> None:
        """Set byte at index."""
        self._value[index] = value
    
    def __getitem__(self, index: int) -> int:
        """Get byte at index."""
        return self._value[index]
    
    def reverse(self) -> None:
        """Reverse bytes in place."""
        self._value.reverse()
