"""Slot for storing local variables, arguments, and static fields."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.vm.types.stack_item import StackItem
    from neo.vm.reference_counter import ReferenceCounter


class Slot:
    """
    Storage slot for variables.

    Used for:
    - Arguments (function parameters)
    - Local variables
    - Static fields

    Reference counting mirrors C# ``Slot`` (neo_csharp_vm/src/Neo.VM/Slot.cs):
    every contained item is a VM stack root, so it holds a stack reference via
    ``ReferenceCounter.AddStackReference``. The sized constructor fills the slot
    with ``Null`` and adds ``count`` stack references in one call (matching
    ``AddStackReference(StackItem.Null, count)``); element replacement removes the
    old reference and adds the new one.
    """

    def __init__(
        self,
        count_or_items: int | list["StackItem"] | None = None,
        reference_counter: "ReferenceCounter" | None = None
    ) -> None:
        from neo.vm.types import NULL
        self._reference_counter = reference_counter
        if isinstance(count_or_items, int):
            # Create slot with `count` NULL items. C# adds the references in a
            # single AddStackReference(Null, count) call.
            count = count_or_items
            self._items: list["StackItem"] = [NULL for _ in range(count)]
            if self._reference_counter is not None and count > 0:
                self._reference_counter.add_stack_reference(NULL, count)
        elif count_or_items is None:
            self._items = []
        else:
            self._items = list(count_or_items)
            for item in self._items:
                self._ref_add(item)

    def _ref_add(self, item: "StackItem") -> None:
        if self._reference_counter is not None:
            self._reference_counter.add_stack_reference(item)

    def _ref_remove(self, item: "StackItem") -> None:
        if self._reference_counter is not None:
            self._reference_counter.remove_stack_reference(item)

    @classmethod
    def from_items(cls, items: list["StackItem"],
                   reference_counter: "ReferenceCounter" | None = None) -> "Slot":
        """Create slot from list of items."""
        return cls(items, reference_counter)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> StackItem:
        return self._items[index]

    def __setitem__(self, index: int, value: "StackItem") -> None:
        old = self._items[index]
        self._ref_remove(old)
        self._items[index] = value
        self._ref_add(value)

    def clear_references(self) -> None:
        """Release the stack references held by every item in the slot.

        Mirrors C# ``Slot.ClearReferences``, called from ``ContextUnloaded`` when
        a context whose slots are no longer reachable is unloaded.
        """
        for item in self._items:
            self._ref_remove(item)
