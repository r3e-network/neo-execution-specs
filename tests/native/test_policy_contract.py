"""Tests for PolicyContract."""

import pytest
from neo.native.policy import (
    PolicyContract, 
    DEFAULT_FEE_PER_BYTE,
    DEFAULT_EXEC_FEE_FACTOR,
    DEFAULT_STORAGE_PRICE
)


class TestPolicyContract:
    """Test PolicyContract functionality."""
    
    def test_name(self):
        """Test contract name."""
        p = PolicyContract()
        assert p.name == "PolicyContract"
    
    def test_default_constants(self):
        """Test default constant values."""
        assert DEFAULT_FEE_PER_BYTE == 1000
        assert DEFAULT_EXEC_FEE_FACTOR == 30
        assert DEFAULT_STORAGE_PRICE == 100000
