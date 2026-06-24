"""Tests for the unified reference counter and removal of the per-stack cap."""

from neo.vm.reference_counter import ReferenceCounter
from neo.vm.evaluation_stack import EvaluationStack
from neo.vm.types import Array, Integer


class TestReferenceCounter:
    """Tests for ReferenceCounter."""

    def test_create(self):
        """Test creating reference counter."""
        rc = ReferenceCounter()
        assert rc is not None

    def test_count(self):
        """Test count property."""
        rc = ReferenceCounter()
        assert rc.count == 0

    def test_eval_stack_drives_count(self):
        """Push/pop on an evaluation stack drive AddStackReference/RemoveStackReference."""
        rc = ReferenceCounter()
        stack = EvaluationStack(rc)
        stack.push(Integer(1))
        stack.push(Integer(2))
        assert rc.count == 2
        stack.pop()
        assert rc.count == 1

    def test_no_per_stack_cap(self):
        """The old 2048-per-evaluation-stack hard cap is gone.

        C# EvaluationStack has no size cap; the only bound is the unified
        ReferenceCounter total checked against MaxStackSize in
        PostExecuteInstruction. Pushing more than 2048 raw items must therefore
        not raise at push time.
        """
        rc = ReferenceCounter()
        stack = EvaluationStack(rc)
        for i in range(3000):
            stack.push(Integer(i))
        assert rc.count == 3000

    def test_circular_reference_terminates(self):
        """A self-referential array must not infinitely recurse and nets per C#."""
        rc = ReferenceCounter()
        stack = EvaluationStack(rc)
        a = Array(rc)
        a.add(a)
        stack.push(a)
        # push: count 0->1 (a), a.stack_references 0->1 (==count) -> recurse
        # add a: count 1->2, a.stack_references 1->2 (!=count) -> stop.
        assert rc.count == 2
        assert a.stack_references == 2
        stack.pop()
        # pop: count 2->1, a.stack_references 2->1 (!=0) -> no recurse.
        assert rc.count == 1
        assert a.stack_references == 1
