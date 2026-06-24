"""Array stack item."""

from __future__ import annotations
from collections.abc import Iterator
from typing import TYPE_CHECKING
from neo.vm.types.stack_item import StackItem, StackItemType

if TYPE_CHECKING:
    from neo.vm.reference_counter import ReferenceCounter


class Array(StackItem):
    """Mutable array on the stack.

    Reference counting follows the C# ``CompoundType`` model
    (neo_csharp_vm/src/Neo.VM/Types/CompoundType.cs): the array tracks how many
    times it is referenced from VM stack roots via ``stack_references``. The
    array mutators do NOT touch the reference counter — that bookkeeping lives in
    the VM jump-table handlers and the recursive ``ReferenceCounter`` traversal,
    exactly like C#. The ``reference_counter`` constructor argument is retained
    for source/API compatibility but is unused.
    """

    __slots__ = ("_items", "_reference_counter", "stack_references")

    def __init__(
        self,
        reference_counter: ReferenceCounter | None = None,
        items: list[StackItem] | None = None
    ) -> None:
        self._reference_counter = reference_counter
        self._items: list[StackItem] = items if items is not None else []
        # C# CompoundType.StackReferences — number of references to this item
        # from the evaluation stacks / slots. Counted lazily by ReferenceCounter.
        self.stack_references: int = 0

    @property
    def type(self) -> StackItemType:
        return StackItemType.ARRAY

    @property
    def is_stack_referenced(self) -> bool:
        """C# ``CompoundType.IsStackReferenced`` (StackReferences != 0)."""
        return self.stack_references != 0

    def sub_items(self) -> Iterator[StackItem]:
        """C# ``CompoundType.SubItems`` — every contained stack item."""
        return iter(self._items)

    def get_boolean(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> StackItem:
        return self._items[index]

    def __setitem__(self, index: int, value: StackItem) -> None:
        self._items[index] = value

    def __iter__(self) -> Iterator[StackItem]:
        return iter(self._items)

    def append(self, item: StackItem) -> None:
        self._items.append(item)

    def add(self, item: StackItem) -> None:
        """Alias for append."""
        self._items.append(item)

    def remove_at(self, index: int) -> None:
        """Remove item at index."""
        del self._items[index]

    def reverse(self) -> None:
        """Reverse items in place."""
        self._items.reverse()

    def clear(self) -> None:
        self._items.clear()
