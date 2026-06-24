"""Tests for the recursive StackReferences reference counter (C# v3.10.0)."""

from neo.vm.reference_counter import ReferenceCounter
from neo.vm.types import Array, Integer


class TestReferenceCounter:
    """Reference counter tests."""

    def test_create(self):
        """Test creation."""
        rc = ReferenceCounter()
        assert rc.count == 0

    def test_add_stack_reference_primitive(self):
        """A primitive item adds exactly one to the total count."""
        rc = ReferenceCounter()
        rc.add_stack_reference(Integer(1))
        assert rc.count == 1

    def test_add_stack_reference_compound_recurses(self):
        """Adding a stack reference to a compound recurses into sub-items.

        Mirrors C# ReferenceCounter.AddStackReference: pushing an array of N
        items counts 1 (the array) + N (its sub-items) and marks the array as
        stack-referenced.
        """
        rc = ReferenceCounter()
        arr = Array(rc, items=[Integer(i) for i in range(3)])
        assert arr.stack_references == 0
        rc.add_stack_reference(arr)
        assert rc.count == 4  # 1 array + 3 sub-items
        assert arr.stack_references == 1
        assert arr.is_stack_referenced

    def test_remove_stack_reference_compound_recurses(self):
        """Removing the last stack reference recurses and nets back to zero."""
        rc = ReferenceCounter()
        arr = Array(rc, items=[Integer(i) for i in range(3)])
        rc.add_stack_reference(arr)
        rc.remove_stack_reference(arr)
        assert rc.count == 0
        assert arr.stack_references == 0
        assert not arr.is_stack_referenced

    def test_add_reference_alias(self):
        """The deprecated add_reference alias delegates to add_stack_reference."""
        rc = ReferenceCounter()
        rc.add_reference(Integer(7))
        assert rc.count == 1
