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
    
    def copy_to(self, target: 'EvaluationStack') -> None:
        """Copy all items to target stack."""
        for item in self._items:
            target.push(item)
    
    def swap(self, i: int, j: int) -> None:
        """Swap items at indices i and j (from top)."""
        idx_i = -(i + 1)
        idx_j = -(j + 1)
        self._items[idx_i], self._items[idx_j] = self._items[idx_j], self._items[idx_i]
    
    def insert(self, index: int, item: StackItem) -> None:
        """Insert item at index (from top)."""
        if len(self._items) >= self._max_size:
            raise StackOverflowException("Stack overflow")
        pos = len(self._items) - index
        self._items.insert(pos, item)
    
    def remove(self, index: int) -> StackItem:
        """Remove and return item at index (from top)."""
        pos = -(index + 1)
        return self._items.pop(pos)
    
    def reverse(self, n: int) -> None:
        """Reverse the top n items on the stack.
        
        Args:
            n: Number of items to reverse from the top
            
        Raises:
            Exception: If n is invalid or exceeds stack size
        """
        if n < 0:
            raise Exception(f"Invalid reverse count: {n}")
        if n > len(self._items):
            raise Exception(f"Insufficient stack items for reverse: need {n}, have {len(self._items)}")
        if n <= 1:
            return
        # Reverse top n items in place
        start = len(self._items) - n
        self._items[start:] = self._items[start:][::-1]
