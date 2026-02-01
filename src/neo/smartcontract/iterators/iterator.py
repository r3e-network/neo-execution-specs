"""IIterator - Iterator interface for smart contracts."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.vm.types import StackItem


class IIterator(ABC):
    """Iterator interface for smart contracts."""
    
    @abstractmethod
    def next(self) -> bool:
        """Advance to next element."""
        pass
    
    @abstractmethod
    def value(self) -> StackItem:
        """Get current element."""
        pass
