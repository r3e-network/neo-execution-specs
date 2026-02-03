"""Integer stack item."""

from __future__ import annotations
from neo.vm.types.stack_item import StackItem, StackItemType
from neo.types import BigInteger


class Integer(StackItem):
    """Integer value on the stack."""
    
    MAX_SIZE = 32  # Maximum bytes for integer representation
    
    ZERO: Integer
    
    __slots__ = ("_value",)
    
    def __init__(self, value: int | BigInteger) -> None:
        big_int = BigInteger(value)
        # Enforce size limit
        byte_len = len(big_int.to_bytes_le())
        if byte_len > self.MAX_SIZE:
            raise OverflowError(f"Integer too large: {byte_len} bytes exceeds maximum {self.MAX_SIZE}")
        self._value = big_int
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.INTEGER
    
    @property
    def value(self) -> BigInteger:
        return self._value
    
    def get_boolean(self) -> bool:
        return self._value != 0
    
    def get_integer(self) -> BigInteger:
        return self._value
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Integer):
            return self._value == other._value
        return False
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def _equals_impl(self, other: "StackItem", limits: object) -> bool:
        """Check equality with another Integer."""
        if isinstance(other, Integer):
            return self._value == other._value
        return False


Integer.ZERO = Integer(0)
