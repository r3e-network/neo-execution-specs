"""Tests for BigInteger."""

import pytest
from neo.types.big_integer import BigInteger


class TestBigInteger:
    """Test BigInteger."""
    
    def test_create(self):
        """Test create."""
        bi = BigInteger(100)
        assert bi is not None
