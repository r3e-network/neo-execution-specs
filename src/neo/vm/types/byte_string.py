"""ByteString stack item."""

from __future__ import annotations
from neo.vm.types.stack_item import StackItem, StackItemType
from neo.types import BigInteger
from neo.exceptions import InvalidOperationException

# Maximum bytes for an integer cast (Integer.MaxSize in C#).
_INTEGER_MAX_SIZE = 32


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
        if any byte in the span is non-zero. C# also rejects values that
        exceed Integer.MaxSize (32 bytes) with an InvalidCastException.
        """
        if len(self._value) > _INTEGER_MAX_SIZE:
            raise InvalidOperationException(
                f"Can not convert ByteString to a boolean, MaxSize of Integer is exceeded: "
                f"{len(self._value)}/{_INTEGER_MAX_SIZE}."
            )
        # Check if any byte is non-zero (matches C# Unsafe.NotZero)
        return any(b != 0 for b in self._value)

    def get_integer(self) -> BigInteger:
        if len(self._value) > _INTEGER_MAX_SIZE:
            raise InvalidOperationException(
                f"Can not convert ByteString to an integer, MaxSize of Integer is exceeded: "
                f"{len(self._value)}/{_INTEGER_MAX_SIZE}."
            )
        return BigInteger.from_bytes_le(self._value)
    
    def get_span(self) -> bytes:
        """Get the raw bytes."""
        return self._value
    
    def get_string(self) -> str:
        """Get as UTF-8 string."""
        return self._value.decode('utf-8')
    
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

    def _equals_impl(self, other: "StackItem", limits: object) -> bool:
        """Content equality with comparable-size enforcement.

        Mirrors C# ByteString.Equals(StackItem, ExecutionEngineLimits) which
        enforces MaxComparableSize and faults when either operand exceeds it.
        The base StackItem.equals has already verified ``other`` is a
        ByteString (same type) and that the two are not identical.
        """
        if not isinstance(other, ByteString):
            return False
        # Resolve the comparable-size budget from the limits object when
        # available; fall back to the module default otherwise.
        from neo.vm.limits import MAX_COMPARABLE_SIZE
        max_size = getattr(limits, "max_comparable_size", MAX_COMPARABLE_SIZE)
        self_size = len(self._value)
        if self_size > max_size or max_size == 0:
            raise InvalidOperationException(
                f"The operand exceeds the maximum comparable size, {self_size}/{max_size}."
            )
        other_size = len(other._value)
        if other_size > max_size:
            raise InvalidOperationException(
                f"The operand exceeds the maximum comparable size, {other_size}/{max_size}."
            )
        return self._value == other._value


ByteString.EMPTY = ByteString(b"")
