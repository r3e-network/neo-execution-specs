"""Evaluation stack for NeoVM."""

from __future__ import annotations
from typing import List, TYPE_CHECKING
from neo.vm.types import StackItem
from neo.exceptions import InvalidOperationException, StackOverflowException

if TYPE_CHECKING:
    from neo.vm.reference_counter import ReferenceCounter


class EvaluationStack:
    """Stack for VM execution."""

    def __init__(self, max_size: int = 2048, reference_counter: ReferenceCounter | None = None) -> None:
        self._items: List[StackItem] = []
        self._max_size = max_size
        self._reference_counter = reference_counter
    
    def __len__(self) -> int:
        return len(self._items)
    
    def push(self, item: StackItem) -> None:
        """Push item onto stack."""
        if len(self._items) >= self._max_size:
            raise StackOverflowException("Stack overflow")
        self._items.append(item)
        if self._reference_counter is not None:
            self._reference_counter.add_reference(item)

    def pop(self) -> StackItem:
        """Pop item from stack.

        Raises:
            Exception: If stack is empty (stack underflow)
        """
        if not self._items:
            raise InvalidOperationException("Stack underflow")
        item = self._items.pop()
        if self._reference_counter is not None:
            self._reference_counter.remove_reference(item)
        return item
    
    def peek(self, index: int = 0) -> StackItem:
        """Peek at item without removing."""
        if index < 0 or index >= len(self._items):
            raise InvalidOperationException(f"Peek index out of range: {index}")
        return self._items[-(index + 1)]
    
    def clear(self) -> None:
        """Clear the stack."""
        if self._reference_counter is not None:
            for item in self._items:
                self._reference_counter.remove_reference(item)
        self._items.clear()
    
    def copy_to(self, target: 'EvaluationStack') -> None:
        """Copy all items to target stack."""
        for item in self._items:
            target.push(item)
    
    def swap(self, i: int, j: int) -> None:
        """Swap items at indices i and j (from top)."""
        if i < 0 or i >= len(self._items):
            raise InvalidOperationException(f"Swap index i out of range: {i}")
        if j < 0 or j >= len(self._items):
            raise InvalidOperationException(f"Swap index j out of range: {j}")
        idx_i = -(i + 1)
        idx_j = -(j + 1)
        self._items[idx_i], self._items[idx_j] = self._items[idx_j], self._items[idx_i]
    
    def insert(self, index: int, item: StackItem) -> None:
        """Insert item at index (from top)."""
        if len(self._items) >= self._max_size:
            raise StackOverflowException("Stack overflow")
        if index < 0 or index > len(self._items):
            raise InvalidOperationException(f"Insert index out of range: {index}")
        pos = len(self._items) - index
        self._items.insert(pos, item)
        if self._reference_counter is not None:
            self._reference_counter.add_reference(item)

    def remove(self, index: int) -> StackItem:
        """Remove and return item at index (from top)."""
        if index < 0 or index >= len(self._items):
            raise InvalidOperationException(f"Remove index out of range: {index}")
        pos = -(index + 1)
        item = self._items.pop(pos)
        if self._reference_counter is not None:
            self._reference_counter.remove_reference(item)
        return item
    
    def reverse(self, n: int) -> None:
        """Reverse the top n items on the stack.
        
        Args:
            n: Number of items to reverse from the top
            
        Raises:
            Exception: If n is invalid or exceeds stack size
        """
        if n < 0:
            raise InvalidOperationException(f"Invalid reverse count: {n}")
        if n > len(self._items):
            raise InvalidOperationException(f"Insufficient stack items for reverse: need {n}, have {len(self._items)}")
        if n <= 1:
            return
        # Reverse top n items in place
        start = len(self._items) - n
        self._items[start:] = self._items[start:][::-1]
