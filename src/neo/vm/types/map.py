"""Map stack item."""

from __future__ import annotations
from collections.abc import Iterator
import itertools
from typing import TYPE_CHECKING
from neo.vm.types.stack_item import StackItem, StackItemType

if TYPE_CHECKING:
    from neo.vm.reference_counter import ReferenceCounter


class Map(StackItem):
    """Key-value map on the stack.

    Reference counting follows the C# ``CompoundType`` model: the map tracks how
    many times it is referenced from VM stack roots via ``stack_references`` and
    does NOT touch the reference counter in its mutators. The counter is driven
    by the jump-table handlers and the recursive ``ReferenceCounter`` traversal.
    """

    __slots__ = ("_items", "_reference_counter", "stack_references")

    def __init__(self, reference_counter: ReferenceCounter | None = None) -> None:
        self._items: dict[StackItem, StackItem] = {}
        self._reference_counter = reference_counter
        self.stack_references: int = 0

    @property
    def type(self) -> StackItemType:
        return StackItemType.MAP

    @property
    def is_stack_referenced(self) -> bool:
        """C# ``CompoundType.IsStackReferenced`` (StackReferences != 0)."""
        return self.stack_references != 0

    def sub_items(self) -> Iterator[StackItem]:
        """C# ``Map.SubItems`` — Keys.Concat(Values)."""
        return itertools.chain(self._items.keys(), self._items.values())

    def get_boolean(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, key: StackItem) -> StackItem:
        return self._items[key]

    def __setitem__(self, key: StackItem, value: StackItem) -> None:
        self._items[key] = value

    def __contains__(self, key: StackItem) -> bool:
        return key in self._items

    def keys(self) -> Iterator[StackItem]:
        return iter(self._items.keys())

    def values(self) -> Iterator[StackItem]:
        return iter(self._items.values())

    def items(self):
        """Return iterator over key-value pairs."""
        return self._items.items()

    def __delitem__(self, key: StackItem) -> None:
        del self._items[key]

    def clear(self) -> None:
        """Clear all items."""
        self._items.clear()
