"""Tests for VM limits enforcement."""

import pytest
from neo.vm.limits import (
    ExecutionEngineLimits,
    MAX_STACK_SIZE,
    MAX_ITEM_SIZE,
    MAX_INVOCATION_STACK_SIZE,
    MAX_SCRIPT_LENGTH,
)


class TestExecutionEngineLimits:
    """Tests for ExecutionEngineLimits class."""
    
    def test_default_values(self):
        """Test default limit values."""
        limits = ExecutionEngineLimits()
        assert limits.max_stack_size == MAX_STACK_SIZE
        assert limits.max_item_size == MAX_ITEM_SIZE
        assert limits.max_invocation_stack_size == MAX_INVOCATION_STACK_SIZE
        assert limits.max_script_length == MAX_SCRIPT_LENGTH
        assert limits.max_try_nesting_depth == 16
    
    def test_custom_values(self):
        """Test custom limit values."""
        limits = ExecutionEngineLimits(
            max_stack_size=100,
            max_item_size=1000,
            max_invocation_stack_size=50,
            max_script_length=5000,
            max_try_nesting_depth=8
        )
        assert limits.max_stack_size == 100
        assert limits.max_item_size == 1000
        assert limits.max_invocation_stack_size == 50
        assert limits.max_script_length == 5000
        assert limits.max_try_nesting_depth == 8
    
    def test_assert_max_item_size_valid(self):
        """Test assert_max_item_size with valid size."""
        limits = ExecutionEngineLimits(max_item_size=1000)
        limits.assert_max_item_size(500)  # Should not raise
        limits.assert_max_item_size(1000)  # Exactly at limit
    
    def test_assert_max_item_size_invalid(self):
        """Test assert_max_item_size with invalid size."""
        limits = ExecutionEngineLimits(max_item_size=1000)
        with pytest.raises(Exception, match="exceeds maximum"):
            limits.assert_max_item_size(1001)
    
    def test_assert_max_stack_size_valid(self):
        """Test assert_max_stack_size with valid size."""
        limits = ExecutionEngineLimits(max_stack_size=100)
        limits.assert_max_stack_size(50)
        limits.assert_max_stack_size(100)
    
    def test_assert_max_stack_size_invalid(self):
        """Test assert_max_stack_size with invalid size."""
        limits = ExecutionEngineLimits(max_stack_size=100)
        with pytest.raises(Exception, match="exceeds maximum"):
            limits.assert_max_stack_size(101)
    
    def test_assert_shift_valid(self):
        """Test assert_shift with valid values."""
        limits = ExecutionEngineLimits()
        limits.assert_shift(0)
        limits.assert_shift(128)
        limits.assert_shift(256)
    
    def test_assert_shift_invalid_negative(self):
        """Test assert_shift with negative value."""
        limits = ExecutionEngineLimits()
        with pytest.raises(Exception, match="out of range"):
            limits.assert_shift(-1)
    
    def test_assert_shift_invalid_too_large(self):
        """Test assert_shift with value > 256."""
        limits = ExecutionEngineLimits()
        with pytest.raises(Exception, match="out of range"):
            limits.assert_shift(257)


class TestLimitConstants:
    """Tests for limit constants."""
    
    def test_max_stack_size(self):
        """Test MAX_STACK_SIZE constant."""
        assert MAX_STACK_SIZE == 2048
    
    def test_max_item_size(self):
        """Test MAX_ITEM_SIZE constant."""
        assert MAX_ITEM_SIZE == 1024 * 1024  # 1 MB
    
    def test_max_invocation_stack_size(self):
        """Test MAX_INVOCATION_STACK_SIZE constant."""
        assert MAX_INVOCATION_STACK_SIZE == 1024
    
    def test_max_script_length(self):
        """Test MAX_SCRIPT_LENGTH constant."""
        assert MAX_SCRIPT_LENGTH == 512 * 1024  # 512 KB
