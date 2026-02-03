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
