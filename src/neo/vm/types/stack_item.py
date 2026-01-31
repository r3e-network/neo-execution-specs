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
