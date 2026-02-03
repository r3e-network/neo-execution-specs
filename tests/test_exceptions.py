"""Tests for Neo exceptions."""

import pytest
from neo.exceptions import (
    NeoException,
    VMException,
    InvalidOperationException,
    OutOfGasException,
    StackOverflowException,
)


class TestNeoException:
    """Tests for NeoException base class."""
    
    def test_basic(self):
        """Test basic exception."""
        ex = NeoException("test error")
        assert str(ex) == "test error"
    
    def test_is_exception(self):
        """Test that NeoException is an Exception."""
        assert issubclass(NeoException, Exception)


class TestVMException:
    """Tests for VMException."""
    
    def test_basic(self):
        """Test basic exception."""
        ex = VMException("vm error")
        assert "vm error" in str(ex)
    
    def test_inheritance(self):
        """Test inheritance."""
        assert issubclass(VMException, NeoException)


class TestInvalidOperationException:
    """Tests for InvalidOperationException."""
    
    def test_basic(self):
        """Test basic exception."""
        ex = InvalidOperationException("invalid op")
        assert "invalid op" in str(ex)
    
    def test_inheritance(self):
        """Test inheritance."""
        assert issubclass(InvalidOperationException, VMException)


class TestOutOfGasException:
    """Tests for OutOfGasException."""
    
    def test_basic(self):
        """Test basic exception."""
        ex = OutOfGasException("out of gas")
        assert "out of gas" in str(ex)
    
    def test_inheritance(self):
        """Test inheritance."""
        assert issubclass(OutOfGasException, VMException)


class TestStackOverflowException:
    """Tests for StackOverflowException."""
    
    def test_basic(self):
        """Test basic exception."""
        ex = StackOverflowException("stack overflow")
        assert "stack overflow" in str(ex)
    
    def test_inheritance(self):
        """Test inheritance."""
        assert issubclass(StackOverflowException, VMException)
