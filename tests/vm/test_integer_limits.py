"""Tests for Integer MAX_SIZE enforcement."""

import pytest
from neo.vm.types import Integer


class TestIntegerMaxSize:
    """Test Integer MAX_SIZE enforcement."""
    
    def test_max_size_constant(self):
        """Test MAX_SIZE constant is 32."""
        assert Integer.MAX_SIZE == 32
    
    def test_within_limit(self):
        """Test values within limit are accepted."""
        # 32 bytes can hold up to 2^255 - 1 positive
        max_positive = 2**255 - 1
        i = Integer(max_positive)
        assert i.get_integer() == max_positive
    
    def test_negative_within_limit(self):
        """Test negative values within limit."""
        max_negative = -(2**255)
        i = Integer(max_negative)
        assert i.get_integer() == max_negative
    
    def test_exceeds_limit(self):
        """Test values exceeding limit raise OverflowError."""
        # 33 bytes needed
        too_large = 2**256
        with pytest.raises(OverflowError):
            Integer(too_large)
    
    def test_negative_exceeds_limit(self):
        """Test negative values exceeding limit."""
        too_small = -(2**256)
        with pytest.raises(OverflowError):
            Integer(too_small)
    
    def test_boundary_32_bytes(self):
        """Test exact 32-byte boundary."""
        # Maximum value that fits in 32 bytes (signed)
        val_31_bytes = 2**247 - 1  # Fits in 31 bytes
        Integer(val_31_bytes)  # Should work
        
        val_32_bytes = 2**255 - 1  # Fits in 32 bytes
        Integer(val_32_bytes)  # Should work
    
    def test_zero(self):
        """Test zero is always valid."""
        i = Integer(0)
        assert i.get_integer() == 0
    
    def test_small_values(self):
        """Test small values work correctly."""
        for v in [-1000, -1, 0, 1, 1000]:
            i = Integer(v)
            assert i.get_integer() == v
