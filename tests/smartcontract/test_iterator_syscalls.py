"""Tests for iterator syscalls."""

import pytest
from neo.smartcontract.iterators import IIterator
from neo.vm.types import Integer, ByteString, InteropInterface


class MockIterator(IIterator):
    """Mock iterator for testing."""
    
    def __init__(self, items):
        self._items = items
        self._index = -1
    
    def next(self) -> bool:
        self._index += 1
        return self._index < len(self._items)
    
    def value(self):
        if self._index < 0 or self._index >= len(self._items):
            raise ValueError("No current element")
        return self._items[self._index]


class TestIteratorNext:
    """Tests for System.Iterator.Next."""
    
    def test_next_returns_true_when_items_available(self):
        """Test that Next returns true when items are available."""
        iterator = MockIterator([Integer(1), Integer(2)])
        assert iterator.next() is True
    
    def test_next_returns_false_when_exhausted(self):
        """Test that Next returns false when iterator is exhausted."""
        iterator = MockIterator([Integer(1)])
        iterator.next()  # Move to first
        assert iterator.next() is False
    
    def test_next_empty_iterator(self):
        """Test Next on empty iterator."""
        iterator = MockIterator([])
        assert iterator.next() is False


class TestIteratorValue:
    """Tests for System.Iterator.Value."""
    
    def test_value_returns_current_item(self):
        """Test that Value returns the current item."""
        items = [Integer(42), ByteString(b"hello")]
        iterator = MockIterator(items)
        iterator.next()
        assert iterator.value() == Integer(42)
    
    def test_value_after_multiple_next(self):
        """Test Value after multiple Next calls."""
        items = [Integer(1), Integer(2), Integer(3)]
        iterator = MockIterator(items)
        iterator.next()
        iterator.next()
        assert iterator.value() == Integer(2)
    
    def test_value_before_next_raises(self):
        """Test that Value raises before Next is called."""
        iterator = MockIterator([Integer(1)])
        with pytest.raises(ValueError):
            iterator.value()


class TestInteropInterface:
    """Tests for InteropInterface with iterators."""
    
    def test_wrap_iterator(self):
        """Test wrapping iterator in InteropInterface."""
        iterator = MockIterator([Integer(1)])
        wrapped = InteropInterface(iterator)
        assert wrapped.get_interface() is iterator
    
    def test_interop_interface_is_truthy(self):
        """Test that InteropInterface is always truthy."""
        iterator = MockIterator([])
        wrapped = InteropInterface(iterator)
        assert wrapped.get_boolean() is True
