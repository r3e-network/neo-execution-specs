"""Tests for exceptions module."""

import pytest
from neo.exceptions import (
    NeoException,
    VMException,
    InvalidOperationException
)


class TestExceptions:
    """Exception tests."""
    
    def test_neo_exception(self):
        """Test NeoException."""
        exc = NeoException("test error")
        assert str(exc) == "test error"
    
    def test_vm_exception(self):
        """Test VMException."""
        exc = VMException("vm error")
        assert str(exc) == "vm error"
