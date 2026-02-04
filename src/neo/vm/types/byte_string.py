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
        """Convert to boolean - True if any byte is non-zero.
        
        This matches C# behavior which uses Unsafe.NotZero() to check
        if any byte in the span is non-zero.
        """
        # Check if any byte is non-zero (matches C# Unsafe.NotZero)
        return any(b != 0 for b in self._value)
    
    def get_integer(self) -> BigInteger:
        return BigInteger.from_bytes_le(self._value)
    
    def get_span(self) -> bytes:
        """Get the raw bytes."""
        return self._value
    
    def get_string(self) -> str:
        """Get as UTF-8 string."""
        return self._value.decode('utf-8', errors='replace')
    
    def __len__(self) -> int:
        return len(self._value)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ByteString):
            return self._value == other._value
        return False
    
    def __hash__(self) -> int:
        """Make ByteString hashable for use as Map keys."""
        return hash(self._value)
    
    def get_bytes_unsafe(self) -> bytes:
        """Get raw bytes without copy."""
        return self._value


ByteString.EMPTY = ByteString(b"")
