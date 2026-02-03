"""Tests for VM limits."""

import pytest
from neo.vm.limits import MAX_STACK_SIZE


def test_limits():
    """Test limit values."""
    assert MAX_STACK_SIZE == 2048
