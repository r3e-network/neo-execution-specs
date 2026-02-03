"""Tests for evaluation stack."""

import pytest
from neo.vm.evaluation_stack import EvaluationStack
from neo.vm.types import Integer, ByteString


class TestEvaluationStack:
    """Evaluation stack tests."""
    
    def test_push_pop(self):
        """Test push and pop."""
        stack = EvaluationStack()
        stack.push(Integer(42))
        result = stack.pop()
        assert result.get_integer() == 42
    
    def test_peek(self):
        """Test peek."""
        stack = EvaluationStack()
        stack.push(Integer(42))
        result = stack.peek()
        assert result.get_integer() == 42
        assert len(stack) == 1
    
    def test_count(self):
        """Test count."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        stack.push(Integer(2))
        assert len(stack) == 2
    
    def test_pop_empty_stack_raises(self):
        """Test pop on empty stack raises exception."""
        stack = EvaluationStack()
        with pytest.raises(Exception, match="Stack underflow"):
            stack.pop()
    
    def test_reverse_top_3(self):
        """Test reverse top 3 items."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        stack.push(Integer(2))
        stack.push(Integer(3))
        # Stack: [1, 2, 3] (3 on top)
        stack.reverse(3)
        # Stack: [3, 2, 1] (1 on top)
        assert stack.pop().get_integer() == 1
        assert stack.pop().get_integer() == 2
        assert stack.pop().get_integer() == 3
    
    def test_reverse_top_4(self):
        """Test reverse top 4 items."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        stack.push(Integer(2))
        stack.push(Integer(3))
        stack.push(Integer(4))
        # Stack: [1, 2, 3, 4] (4 on top)
        stack.reverse(4)
        # Stack: [4, 3, 2, 1] (1 on top)
        assert stack.pop().get_integer() == 1
        assert stack.pop().get_integer() == 2
        assert stack.pop().get_integer() == 3
        assert stack.pop().get_integer() == 4
    
    def test_reverse_n_items(self):
        """Test reverse n items (partial stack)."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        stack.push(Integer(2))
        stack.push(Integer(3))
        stack.push(Integer(4))
        stack.push(Integer(5))
        # Stack: [1, 2, 3, 4, 5] (5 on top)
        stack.reverse(3)  # Reverse only top 3
        # Stack: [1, 2, 5, 4, 3] (3 on top)
        assert stack.pop().get_integer() == 3
        assert stack.pop().get_integer() == 4
        assert stack.pop().get_integer() == 5
        assert stack.pop().get_integer() == 2
        assert stack.pop().get_integer() == 1
    
    def test_reverse_zero(self):
        """Test reverse 0 items does nothing."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        stack.reverse(0)
        assert stack.pop().get_integer() == 1
    
    def test_reverse_one(self):
        """Test reverse 1 item does nothing."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        stack.reverse(1)
        assert stack.pop().get_integer() == 1
    
    def test_reverse_invalid_count(self):
        """Test reverse with invalid count raises."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        with pytest.raises(Exception):
            stack.reverse(5)  # More than stack size
        with pytest.raises(Exception):
            stack.reverse(-1)  # Negative
