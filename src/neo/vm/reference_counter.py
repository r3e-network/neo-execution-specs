"""Reference counter for preventing circular reference DoS attacks.

Tracks references between compound types (Array, Map, Struct) to enforce
stack item count limits and detect zero-referenced items.

Uses id() -> (strong_ref, count) mapping to prevent GC id reuse.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.vm.types.stack_item import StackItem

class ReferenceCounter:
    """
    Tracks references between compound types to prevent circular reference attacks.

    When a compound type (Array, Struct, Map) references another item,
    the reference is tracked. Items with zero references can be collected.

    Implementation note: We store (object_ref, count) tuples keyed by id()
    to hold strong references, preventing Python GC from reclaiming objects
    and reusing their id() values.
    """

    def __init__(self) -> None:
        # id(item) -> (item_ref, ref_count) — strong ref prevents id reuse
        self._tracked: dict[int, tuple[StackItem, int]] = {}
        self._zero_referred: set[int] = set()
        self._count: int = 0

    @property
    def count(self) -> int:
        """Total tracked items."""
        return self._count

    def add_reference(self, item: StackItem) -> None:
        """Add a reference to an item."""
        item_id = id(item)
        if item_id in self._tracked:
            obj, ref_count = self._tracked[item_id]
            self._tracked[item_id] = (obj, ref_count + 1)
            self._zero_referred.discard(item_id)
        else:
            self._tracked[item_id] = (item, 1)
            self._count += 1

    def remove_reference(self, item: StackItem) -> None:
        """Remove a reference from an item."""
        item_id = id(item)
        if item_id not in self._tracked:
            return

        obj, ref_count = self._tracked[item_id]
        new_count = ref_count - 1
        if new_count <= 0:
            self._zero_referred.add(item_id)
            self._tracked[item_id] = (obj, 0)
        else:
            self._tracked[item_id] = (obj, new_count)

    def check_zero_referred(self) -> int:
        """Remove and return count of items with zero references."""
        count = len(self._zero_referred)
        for item_id in self._zero_referred:
            if item_id in self._tracked:
                del self._tracked[item_id]
                self._count -= 1
        self._zero_referred.clear()
        return count
