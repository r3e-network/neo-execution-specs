"""Evaluation stack for NeoVM."""

from __future__ import annotations
from typing import List, Optional
from neo.vm.types import StackItem
from neo.exceptions import StackOverflowException


class EvaluationStack:
    """Stack for VM execution."""
    
    def __init__(self, max_size: int = 2048) -> None:
        self._items: List[StackItem] = []
        self._max_size = max_size
    
    def __len__(self) -> int:
        return len(self._items)
    
    def push(self, item: StackItem) -> None:
        """Push item onto stack."""
        if len(self._items) >= self._max_size:
            raise StackOverflowException("Stack overflow")
        self._items.append(item)
    
    def pop(self) -> StackItem:
        """Pop item from stack."""
        return self._items.pop()
    
    def peek(self, index: int = 0) -> StackItem:
        """Peek at item without removing."""
        return self._items[-(index + 1)]
    
    def clear(self) -> None:
        """Clear the stack."""
        self._items.clear()
