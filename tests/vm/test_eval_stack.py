"""Tests for evaluation stack."""

from neo.vm.evaluation_stack import EvaluationStack
from neo.vm.types import Integer


class TestEvaluationStack:
    """Tests for EvaluationStack."""
    
    def test_create_empty(self):
        """Test creating empty stack."""
        stack = EvaluationStack()
        assert len(stack) == 0
    
    def test_push_pop(self):
        """Test push and pop."""
        stack = EvaluationStack()
        stack.push(Integer(42))
        assert len(stack) == 1
        item = stack.pop()
        assert item.get_integer() == 42
    
    def test_peek(self):
        """Test peek."""
        stack = EvaluationStack()
        stack.push(Integer(1))
        stack.push(Integer(2))
        assert stack.peek().get_integer() == 2
        assert len(stack) == 2
