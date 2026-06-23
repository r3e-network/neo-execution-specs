"""Struct stack item."""

from __future__ import annotations
from neo.vm.types.array import Array
from neo.vm.types.stack_item import StackItem, StackItemType
from neo.exceptions import InvalidOperationException


class Struct(Array):
    """Struct - similar to Array but with value semantics for cloning."""

    @property
    def type(self) -> StackItemType:
        return StackItemType.STRUCT

    def clone(self) -> Struct:
        """Create a deep copy of this struct (recursively clones nested Structs)."""
        result = Struct()
        for item in self._items:
            if isinstance(item, Struct):
                result.add(item.clone())
            else:
                result.add(item)
        return result

    def _equals_impl(self, other: "StackItem", limits: object) -> bool:
        """Structural deep comparison (mirrors C# Struct.Equals with limits).

        The base StackItem.equals has already established ``other`` is a Struct
        (same type) and the two are not identical. C# Struct.Equals(StackItem)
        without limits throws NotSupported; the limits overload performs an
        iterative deep comparison bounded by MaxStackSize / MaxComparableSize.
        """
        from neo.vm.types.byte_string import ByteString
        from neo.vm.limits import MAX_STACK_SIZE, MAX_COMPARABLE_SIZE

        if not isinstance(other, Struct):
            return False

        max_stack_size = getattr(limits, "max_stack_size", MAX_STACK_SIZE)
        max_comparable_size = getattr(limits, "max_comparable_size", MAX_COMPARABLE_SIZE)

        stack1: list[StackItem] = [self]
        stack2: list[StackItem] = [other]
        count = max_stack_size
        while stack1:
            if count == 0:
                raise InvalidOperationException(
                    "Too many struct items to compare in struct comparison."
                )
            count -= 1
            a = stack1.pop()
            b = stack2.pop()
            if isinstance(a, ByteString):
                # Debit the comparable-size budget exactly as ByteString does
                # (max(size_a, size_b, 1)) and fault when exhausted, matching
                # C# ByteString.Equals(StackItem, ref maxComparableSize).
                if not isinstance(b, ByteString):
                    return False
                size_a = len(a.value)
                if size_a > max_comparable_size or max_comparable_size == 0:
                    raise InvalidOperationException(
                        f"The operand exceeds the maximum comparable size, "
                        f"{size_a}/{max_comparable_size}."
                    )
                compared_size = max(size_a, len(b.value), 1)
                if a is not b and len(b.value) > max_comparable_size:
                    raise InvalidOperationException(
                        f"The operand exceeds the maximum comparable size, "
                        f"{len(b.value)}/{max_comparable_size}."
                    )
                equal = (a is b) or (a.value == b.value)
                max_comparable_size -= compared_size
                if not equal:
                    return False
            else:
                if max_comparable_size == 0:
                    raise InvalidOperationException(
                        "The operand exceeds the maximum comparable size in struct comparison."
                    )
                max_comparable_size -= 1
                if isinstance(a, Struct):
                    if a is b:
                        continue
                    if not isinstance(b, Struct):
                        return False
                    if len(a) != len(b):
                        return False
                    for item in a:
                        stack1.append(item)
                    for item in b:
                        stack2.append(item)
                else:
                    if not a.equals(b):
                        return False
        return True
