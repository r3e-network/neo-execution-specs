"""ByteString stack item."""

from __future__ import annotations
from neo.vm.types.stack_item import StackItem, StackItemType
from neo.types import BigInteger


class ByteString(StackItem):
    """Immutable byte sequence on the stack."""
    
    EMPTY: ByteString
    
    __slots__ = ("_value",)
    
    def __init__(self, value: bytes = b"") -> None:
        self._value = value
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.BYTESTRING
    
    @property
    def value(self) -> bytes:
        return self._value
    
    def get_boolean(self) -> bool:
        return len(self._value) > 0
    
    def get_integer(self) -> BigInteger:
        return BigInteger.from_bytes_le(self._value)
    
    def __len__(self) -> int:
        return len(self._value)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ByteString):
            return self._value == other._value
        return False


ByteString.EMPTY = ByteString(b"")
