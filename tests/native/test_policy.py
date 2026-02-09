"""Tests for Policy native contract."""

from neo.native.policy import (
    PolicyContract,
    DEFAULT_EXEC_FEE_FACTOR,
    DEFAULT_STORAGE_PRICE,
    DEFAULT_FEE_PER_BYTE,
    MAX_EXEC_FEE_FACTOR,
    MAX_STORAGE_PRICE,
)


class TestPolicyContract:
    """Tests for PolicyContract."""
    
    def test_name(self):
        """Test contract name."""
        policy = PolicyContract()
        assert policy.name == "PolicyContract"
    
    def test_default_constants(self):
        """Test default constant values."""
        assert DEFAULT_EXEC_FEE_FACTOR == 30
        assert DEFAULT_STORAGE_PRICE == 100000
        assert DEFAULT_FEE_PER_BYTE == 1000
    
    def test_max_constants(self):
        """Test maximum constant values."""
        assert MAX_EXEC_FEE_FACTOR == 100
        assert MAX_STORAGE_PRICE == 10000000
