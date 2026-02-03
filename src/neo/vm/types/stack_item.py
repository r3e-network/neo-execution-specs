"""StackItem base class."""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.types import BigInteger


class StackItemType(IntEnum):
    """Stack item types."""
    ANY = 0x00
    POINTER = 0x10
    BOOLEAN = 0x20
    INTEGER = 0x21
    BYTESTRING = 0x28
    BUFFER = 0x30
    ARRAY = 0x40
    STRUCT = 0x41
    MAP = 0x48
    INTEROP_INTERFACE = 0x60


class StackItem(ABC):
    """Base class for all stack items."""
    
    @property
    @abstractmethod
    def type(self) -> StackItemType:
        """Get the stack item type."""
        ...
    
    @abstractmethod
    def get_boolean(self) -> bool:
        """Convert to boolean."""
        ...
    
    def get_integer(self) -> BigInteger:
        """Convert to integer."""
        from neo.types import BigInteger
        raise TypeError(f"Cannot convert {self.type} to Integer")
    
    def get_bytes_unsafe(self) -> bytes:
        """Get raw bytes without copy."""
        raise TypeError(f"Cannot get bytes from {self.type}")
    
    def equals(self, other: "StackItem", limits: object = None) -> bool:
        """Check equality with another stack item."""
        if self is other:
            return True
        if self.type != other.type:
            return False
        return self._equals_impl(other, limits)
    
    def _equals_impl(self, other: "StackItem", limits: object) -> bool:
        """Implementation-specific equality check."""
        return False
    
    @property
    def is_null(self) -> bool:
        """Check if this is a null value."""
        return False
