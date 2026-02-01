"""InteropInterface type for NeoVM.

InteropInterface wraps external objects that can be passed to and from
the VM through system calls (SYSCALL). These objects are opaque to the
VM and can only be manipulated through interop services.
"""

from __future__ import annotations
from typing import Any, TypeVar, Generic

from .stack_item import StackItem, StackItemType

T = TypeVar('T')


class InteropInterface(StackItem, Generic[T]):
    """Represents an interop interface wrapping an external object.
    
    InteropInterface is used to pass objects between the VM and external
    services. The wrapped object is opaque to the VM - it cannot be
    inspected or modified directly, only passed to syscalls.
    
    Attributes:
        _object: The wrapped external object.
    """
    
    __slots__ = ('_object',)
    
    def __init__(self, obj: T) -> None:
        """Initialize a new InteropInterface.
        
        Args:
            obj: The object to wrap.
        """
        self._object = obj
    
    @property
    def type(self) -> StackItemType:
        """Get the stack item type."""
        return StackItemType.INTEROP_INTERFACE
    
    def get_interface(self) -> T:
        """Get the wrapped object.
        
        Returns:
            The wrapped external object.
        """
        return self._object
    
    def get_boolean(self) -> bool:
        """Convert to boolean.
        
        InteropInterface is always truthy.
        """
        return True
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another object."""
        if not isinstance(other, InteropInterface):
            return False
        return self._object is other._object
    
    def __hash__(self) -> int:
        """Get hash value."""
        return hash(id(self._object))
    
    def __repr__(self) -> str:
        """Get string representation."""
        return f"InteropInterface({type(self._object).__name__})"
