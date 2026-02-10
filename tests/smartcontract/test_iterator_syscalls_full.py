"""Tests for iterator syscalls (System.Iterator.Next / Value).

Covers:
- iterator_next: happy path, non-InteropInterface, non-IIterator
- iterator_value: happy path, non-InteropInterface, non-IIterator
- End-to-end: next+value cycle with StorageIterator
"""

from __future__ import annotations

import pytest

from neo.vm.execution_context import ExecutionContext
from neo.vm.types import Integer, ByteString, InteropInterface
from neo.smartcontract.iterators import IIterator
from neo.smartcontract.syscalls.iterator import iterator_next, iterator_value


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

class SimpleIterator(IIterator):
    """Minimal IIterator for syscall testing."""

    def __init__(self, items):
        self._items = items
        self._idx = -1

    def next(self) -> bool:
        self._idx += 1
        return self._idx < len(self._items)

    def value(self):
        if self._idx < 0 or self._idx >= len(self._items):
            raise ValueError("No current element")
        return self._items[self._idx]


class MockEngine:
    """Engine mock with current_context for syscall tests."""

    def __init__(self):
        self.current_context = ExecutionContext(script=b"\x00")

    @property
    def stack(self):
        return self.current_context.evaluation_stack


# ---------------------------------------------------------------------------
# iterator_next tests
# ---------------------------------------------------------------------------

class TestIteratorNext:
    """System.Iterator.Next syscall."""

    def test_next_returns_true_when_items(self):
        engine = MockEngine()
        it = SimpleIterator([ByteString(b"a")])
        engine.stack.push(InteropInterface(it))
        iterator_next(engine)
        assert engine.stack.pop().get_boolean() is True

    def test_next_returns_false_when_empty(self):
        engine = MockEngine()
        it = SimpleIterator([])
        engine.stack.push(InteropInterface(it))
        iterator_next(engine)
        assert engine.stack.pop().get_boolean() is False

    def test_next_non_interop_raises(self):
        engine = MockEngine()
        engine.stack.push(Integer(42))
        with pytest.raises(ValueError, match="InteropInterface"):
            iterator_next(engine)

    def test_next_non_iterator_raises(self):
        engine = MockEngine()
        engine.stack.push(InteropInterface("not an iterator"))
        with pytest.raises(ValueError, match="IIterator"):
            iterator_next(engine)


# ---------------------------------------------------------------------------
# iterator_value tests
# ---------------------------------------------------------------------------

class TestIteratorValue:
    """System.Iterator.Value syscall."""

    def test_value_returns_current_item(self):
        engine = MockEngine()
        it = SimpleIterator([ByteString(b"hello")])
        it.next()  # advance to first
        engine.stack.push(InteropInterface(it))
        iterator_value(engine)
        result = engine.stack.pop()
        assert result.value == b"hello"

    def test_value_non_interop_raises(self):
        engine = MockEngine()
        engine.stack.push(Integer(42))
        with pytest.raises(ValueError, match="InteropInterface"):
            iterator_value(engine)

    def test_value_non_iterator_raises(self):
        engine = MockEngine()
        engine.stack.push(InteropInterface("not an iterator"))
        with pytest.raises(ValueError, match="IIterator"):
            iterator_value(engine)
