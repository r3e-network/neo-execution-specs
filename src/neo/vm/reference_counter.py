"""Reference counter for VM stack-item accounting.

Faithful port of C# Neo.VM ``ReferenceCounter`` (v3.10.0,
neo_csharp_vm/src/Neo.VM/ReferenceCounter.cs). The model is the recursive
*StackReferences* model:

* A single integer ``Count`` tracks the total number of references currently
  reachable from VM *stack roots* (evaluation stacks and slots).
* ``add_stack_reference(item, count)`` is called when ``item`` is pushed onto an
  evaluation stack or stored in a slot. It increments ``Count`` and, for a
  :class:`CompoundType`, bumps the item's ``stack_references``. The first time a
  compound becomes stack-referenced (``stack_references`` transitions to
  ``count``), the reference is propagated recursively to every sub-item.
* ``remove_stack_reference(item)`` reverses that: it decrements ``Count`` and, for
  a compound, decrements ``stack_references``; when that reaches zero the removal
  is propagated recursively to every sub-item.
* ``post_execute_instruction(limits)`` runs after each instruction and faults when
  ``Count`` exceeds ``MaxStackSize``.

Compound *element edges* (SETITEM / APPEND / REMOVE / PACK / ...) only adjust the
counter through the jump-table handlers, and only while the host compound is
itself stack-referenced (``is_stack_referenced``) — exactly mirroring
``JumpTable.Compound.cs``. The compound type mutators therefore do NOT touch the
reference counter directly.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.exceptions import InvalidOperationException

if TYPE_CHECKING:
    from neo.vm.limits import ExecutionEngineLimits
    from neo.vm.types.stack_item import StackItem


def _is_compound(item: "StackItem") -> bool:
    """Return True if ``item`` is a VM CompoundType (Array/Struct/Map).

    Imported lazily to avoid a circular import at module load time.
    """
    from neo.vm.types.array import Array
    from neo.vm.types.map import Map

    return isinstance(item, (Array, Map))


class ReferenceCounter:
    """Tracks the total reference count of VM stack items.

    Port of C# ``ReferenceCounter`` (v3.10.0). ``Count`` equals the number of
    references held by evaluation stacks, slots, and the compound child edges
    reachable from them.
    """

    def __init__(self) -> None:
        self._references_count: int = 0

    @property
    def count(self) -> int:
        """Total reference count (C# ``ReferenceCounter.Count``)."""
        return self._references_count

    def add_stack_reference(self, item: "StackItem", count: int = 1) -> None:
        """Add ``count`` stack references to ``item``.

        Mirrors C# ``ReferenceCounter.AddStackReference``: increments the total
        count, and for a compound type bumps its ``stack_references`` — recursing
        into sub-items the first time the compound becomes stack-referenced.
        """
        self._references_count += count

        if _is_compound(item):
            item.stack_references += count
            if item.stack_references == count:
                for sub_item in item.sub_items():
                    self.add_stack_reference(sub_item)

    def remove_stack_reference(self, item: "StackItem") -> None:
        """Remove a single stack reference from ``item``.

        Mirrors C# ``ReferenceCounter.RemoveStackReference``: decrements the total
        count, and for a compound type decrements its ``stack_references`` —
        recursing into sub-items once the compound is no longer stack-referenced.
        """
        self._references_count -= 1

        if _is_compound(item):
            item.stack_references -= 1
            if item.stack_references == 0:
                for sub_item in item.sub_items():
                    self.remove_stack_reference(sub_item)

    def post_execute_instruction(self, limits: "ExecutionEngineLimits") -> None:
        """Enforce the global MaxStackSize bound after each instruction.

        Mirrors C# ``ReferenceCounter.PostExecuteInstruction``
        (ReferenceCounter.cs:57-61): faults when the total reference count
        exceeds ``Limits.MaxStackSize``. Called from
        ``ExecutionEngine.execute_next`` after the opcode handler so the FAULT is
        routed exactly like other engine errors.
        """
        if self._references_count > limits.max_stack_size:
            raise InvalidOperationException(
                f"MaxStackSize exceed: {self._references_count}/{limits.max_stack_size}"
            )

    # ------------------------------------------------------------------
    # Backwards-compatible aliases.
    #
    # The historical Python API exposed ``add_reference`` / ``remove_reference``.
    # C# v3.10.0 unifies these into the stack-reference API; the aliases are kept
    # so external/test callers that pass a raw item keep working.
    # ------------------------------------------------------------------
    def add_reference(self, item: "StackItem", *_unused: object) -> None:
        """Deprecated alias for :meth:`add_stack_reference` (count=1)."""
        self.add_stack_reference(item)

    def remove_reference(self, item: "StackItem", *_unused: object) -> None:
        """Deprecated alias for :meth:`remove_stack_reference`."""
        self.remove_stack_reference(item)
