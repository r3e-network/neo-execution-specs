"""Tests for interop service."""

import pytest
from neo.smartcontract.interop_service import (
    get_interop_hash,
    register_syscall,
    get_syscall,
)


class TestInteropService:
    """Test interop service."""
    
    def test_get_interop_hash(self):
        """Test syscall hash calculation."""
        # Known hash for System.Runtime.GetTrigger
        hash_val = get_interop_hash("System.Runtime.GetTrigger")
        assert isinstance(hash_val, int)
        assert hash_val > 0
