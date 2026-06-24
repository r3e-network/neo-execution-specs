"""Evaluation stack for NeoVM."""

from __future__ import annotations
from typing import TYPE_CHECKING
from neo.vm.types import StackItem
from neo.exceptions import InvalidOperationException

if TYPE_CHECKING:
    from neo.vm.reference_counter import ReferenceCounter


class EvaluationStack:
    """Stack for VM execution.

    Mirrors C# ``EvaluationStack`` (neo_csharp_vm/src/Neo.VM/EvaluationStack.cs).
    There is intentionally NO per-stack size cap: the only bound on the number of
    items reachable from VM stack roots is the unified ``ReferenceCounter`` total,
    enforced against ``MaxStackSize`` in ``PostExecuteInstruction`` after each
    instruction. Push/insert add a stack reference; pop/remove/clear remove one.
    """

    def __init__(self, reference_counter: ReferenceCounter | None = None) -> None:
        self._items: list[StackItem] = []
        self._reference_counter = reference_counter

    def __len__(self) -> int:
        return len(self._items)

    def _ref_add(self, item: StackItem) -> None:
        if self._reference_counter is not None:
            self._reference_counter.add_stack_reference(item)

    def _ref_remove(self, item: StackItem) -> None:
        if self._reference_counter is not None:
            self._reference_counter.remove_stack_reference(item)

    def push(self, item: StackItem) -> None:
        """Push item onto stack (C# ``Push`` → ``AddStackReference``)."""
        self._items.append(item)
        self._ref_add(item)

    def pop(self) -> StackItem:
        """Pop item from stack.

        Raises:
            Exception: If stack is empty (stack underflow)
        """
        if not self._items:
            raise InvalidOperationException("Stack underflow")
        item = self._items.pop()
        self._ref_remove(item)
        return item

    def peek(self, index: int = 0) -> StackItem:
        """Peek at item without removing."""
        if index < 0 or index >= len(self._items):
            raise InvalidOperationException(f"Peek index out of range: {index}")
        return self._items[-(index + 1)]

    def clear(self) -> None:
        """Clear the stack (C# ``Clear`` → RemoveStackReference per item)."""
        for item in self._items:
            self._ref_remove(item)
        self._items.clear()

    def copy_to(self, target: 'EvaluationStack') -> None:
        """Move all items to ``target`` without changing reference counts.

        Mirrors C# ``EvaluationStack.CopyTo`` (AddRange on the inner list): each
        item simply transfers its existing single stack reference to the target
        stack. The source stack is abandoned afterwards (RET drops it), so NO
        AddStackReference/RemoveStackReference is performed — doing so would
        double-count or under-count the reference total.
        """
        target._items.extend(self._items)

    def swap(self, i: int, j: int) -> None:
        """Swap items at indices i and j (from top).

        O(1) and does not touch reference counting (items stay on the stack),
        matching C# ``EvaluationStack.Swap``.
        """
        if i < 0 or i >= len(self._items):
            raise InvalidOperationException(f"Swap index i out of range: {i}")
        if j < 0 or j >= len(self._items):
            raise InvalidOperationException(f"Swap index j out of range: {j}")
        idx_i = -(i + 1)
        idx_j = -(j + 1)
        self._items[idx_i], self._items[idx_j] = self._items[idx_j], self._items[idx_i]

    def insert(self, index: int, item: StackItem) -> None:
        """Insert item at index (from top) (C# ``Insert`` → AddStackReference)."""
        if index < 0 or index > len(self._items):
            raise InvalidOperationException(f"Insert index out of range: {index}")
        pos = len(self._items) - index
        self._items.insert(pos, item)
        self._ref_add(item)

    def remove(self, index: int) -> StackItem:
        """Remove and return item at index (from top)."""
        if index < 0 or index >= len(self._items):
            raise InvalidOperationException(f"Remove index out of range: {index}")
        pos = -(index + 1)
        item = self._items.pop(pos)
        self._ref_remove(item)
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
