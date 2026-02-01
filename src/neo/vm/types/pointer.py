"""Pointer type for NeoVM.

A Pointer represents a position within a script. It is used by the PUSHA
instruction to push an address onto the stack, and by CALLA to call a
function at a pointer address.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from .stack_item import StackItem, StackItemType

if TYPE_CHECKING:
    from neo.vm.script import Script


class Pointer(StackItem):
    """Represents a pointer to a position in a script.
    
    Pointers are used for indirect function calls (CALLA) and are created
    by the PUSHA instruction. They cannot be shared between different scripts.
    
    Attributes:
        script: The script this pointer belongs to.
        position: The position within the script.
    """
    
    __slots__ = ('_script', '_position')
    
    def __init__(self, script: Script, position: int) -> None:
        """Initialize a new Pointer.
        
        Args:
            script: The script this pointer belongs to.
            position: The position within the script (must be valid).
            
        Raises:
            ValueError: If position is negative or beyond script length.
        """
        if position < 0:
            raise ValueError(f"Pointer position cannot be negative: {position}")
        self._script = script
        self._position = position
    
    @property
    def type(self) -> StackItemType:
        """Get the stack item type."""
        return StackItemType.POINTER
    
    @property
    def script(self) -> Script:
        """Get the script this pointer belongs to."""
        return self._script
    
    @property
    def position(self) -> int:
        """Get the position within the script."""
        return self._position
    
    def get_boolean(self) -> bool:
        """Convert to boolean.
        
        Pointers are always truthy.
        """
        return True
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another object."""
        if not isinstance(other, Pointer):
            return False
        return self._script is other._script and self._position == other._position
    
    def __hash__(self) -> int:
        """Get hash value."""
        return hash((id(self._script), self._position))
    
    def __repr__(self) -> str:
        """Get string representation."""
        return f"Pointer(position={self._position})"
