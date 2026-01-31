"""Tests for UInt160."""

import pytest
from neo.types import UInt160


def test_uint160_zero():
    """Test zero value."""
    zero = UInt160.ZERO
    assert len(zero.data) == 20
    assert zero.data == b"\x00" * 20


def test_uint160_from_bytes():
    """Test creation from bytes."""
    data = bytes(range(20))
    u = UInt160(data)
    assert u.data == data


def test_uint160_invalid_length():
    """Test invalid length raises error."""
    with pytest.raises(ValueError):
        UInt160(b"\x00" * 10)
