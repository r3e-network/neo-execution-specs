"""Tests for exception handling (TRY/CATCH/FINALLY)."""

import pytest
from neo.vm.exception_handling import (
    ExceptionHandlingContext,
    ExceptionHandlingState,
    TryStack,
)


class TestExceptionHandlingContext:
    """Tests for ExceptionHandlingContext."""
    
    def test_context_creation(self):
        """Test creating an exception handling context."""
        ctx = ExceptionHandlingContext(catch_pointer=10, finally_pointer=20)
        assert ctx.catch_pointer == 10
        assert ctx.finally_pointer == 20
        assert ctx.end_pointer == -1
        assert ctx.state == ExceptionHandlingState.TRY
    
    def test_has_catch(self):
        """Test has_catch property."""
        ctx_with_catch = ExceptionHandlingContext(catch_pointer=10, finally_pointer=-1)
        ctx_without_catch = ExceptionHandlingContext(catch_pointer=-1, finally_pointer=20)
        
        assert ctx_with_catch.has_catch is True
        assert ctx_without_catch.has_catch is False
    
    def test_has_finally(self):
        """Test has_finally property."""
        ctx_with_finally = ExceptionHandlingContext(catch_pointer=-1, finally_pointer=20)
        ctx_without_finally = ExceptionHandlingContext(catch_pointer=10, finally_pointer=-1)
        
        assert ctx_with_finally.has_finally is True
        assert ctx_without_finally.has_finally is False
    
    def test_state_transitions(self):
        """Test state transitions."""
        ctx = ExceptionHandlingContext(catch_pointer=10, finally_pointer=20)
        
        assert ctx.state == ExceptionHandlingState.TRY
        ctx.state = ExceptionHandlingState.CATCH
        assert ctx.state == ExceptionHandlingState.CATCH
        ctx.state = ExceptionHandlingState.FINALLY
        assert ctx.state == ExceptionHandlingState.FINALLY


class TestTryStack:
    """Tests for TryStack."""
    
    def test_empty_stack(self):
        """Test empty try stack."""
        stack = TryStack()
        assert len(stack) == 0
        assert not stack
        assert stack.peek() is None
    
    def test_push_and_pop(self):
        """Test push and pop operations."""
        stack = TryStack()
        ctx = ExceptionHandlingContext(catch_pointer=10, finally_pointer=20)
        
        stack.push(ctx)
        assert len(stack) == 1
        assert stack
        
        popped = stack.pop()
        assert popped is ctx
        assert len(stack) == 0
    
    def test_peek(self):
        """Test peek operation."""
        stack = TryStack()
        ctx = ExceptionHandlingContext(catch_pointer=10, finally_pointer=20)
        
        stack.push(ctx)
        peeked = stack.peek()
        assert peeked is ctx
        assert len(stack) == 1  # Still on stack
    
    def test_try_peek(self):
        """Test try_peek operation."""
        stack = TryStack()
        
        success, ctx = stack.try_peek()
        assert success is False
        assert ctx is None
        
        new_ctx = ExceptionHandlingContext(catch_pointer=10, finally_pointer=20)
        stack.push(new_ctx)
        
        success, ctx = stack.try_peek()
        assert success is True
        assert ctx is new_ctx
    
    def test_try_pop(self):
        """Test try_pop operation."""
        stack = TryStack()
        
        success, ctx = stack.try_pop()
        assert success is False
        assert ctx is None
        
        new_ctx = ExceptionHandlingContext(catch_pointer=10, finally_pointer=20)
        stack.push(new_ctx)
        
        success, ctx = stack.try_pop()
        assert success is True
        assert ctx is new_ctx
        assert len(stack) == 0
    
    def test_nested_try_blocks(self):
        """Test nested try blocks."""
        stack = TryStack()
        ctx1 = ExceptionHandlingContext(catch_pointer=10, finally_pointer=20)
        ctx2 = ExceptionHandlingContext(catch_pointer=30, finally_pointer=40)
        
        stack.push(ctx1)
        stack.push(ctx2)
        
        assert len(stack) == 2
        assert stack.peek() is ctx2
        
        stack.pop()
        assert stack.peek() is ctx1
