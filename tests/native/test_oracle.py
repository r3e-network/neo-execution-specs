"""Tests for native contracts."""

import pytest
from neo.native.oracle_response import OracleResponseCode


class TestOracle:
    """Oracle tests."""
    
    def test_response_codes(self):
        """Test response codes."""
        assert OracleResponseCode.SUCCESS == 0
        assert OracleResponseCode.ERROR == 0xff
