"""Iterator syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Iterator.cs
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


def iterator_next(engine: "ApplicationEngine") -> None:
    """System.Iterator.Next
    
    Advances the iterator to the next element.
    
    Stack: [iterator] -> [bool]
    """
    from neo.vm.types import Boolean, InteropInterface
    from neo.smartcontract.iterators import IIterator
    
    stack = engine.current_context.evaluation_stack
    
    # Pop iterator from stack
    item = stack.pop()
    
    if not isinstance(item, InteropInterface):
        raise ValueError("Expected InteropInterface")
    
    iterator = item.get_interface()
    
    if not isinstance(iterator, IIterator):
        raise ValueError("Expected IIterator")
    
    # Advance iterator
    result = iterator.next()
    
    stack.push(Boolean(result))


def iterator_value(engine: "ApplicationEngine") -> None:
    """System.Iterator.Value
    
    Gets the element at the current position of the iterator.
    
    Stack: [iterator] -> [value]
    """
    from neo.vm.types import InteropInterface
    from neo.smartcontract.iterators import IIterator
    
    stack = engine.current_context.evaluation_stack
    
    # Pop iterator from stack
    item = stack.pop()
    
    if not isinstance(item, InteropInterface):
        raise ValueError("Expected InteropInterface")
    
    iterator = item.get_interface()
    
    if not isinstance(iterator, IIterator):
        raise ValueError("Expected IIterator")
    
    # Get current value
    value = iterator.value()
    
    stack.push(value)
