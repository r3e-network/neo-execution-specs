"""Tests for Neo exceptions."""

from neo.exceptions import (
    NeoException,
    VMException,
    InvalidOperationException,
    OutOfGasException,
    StackOverflowException,
    VMAbortException,
    CryptoException,
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


class TestVMAbortException:
    """Tests for VMAbortException."""

    def test_basic(self):
        ex = VMAbortException("abort")
        assert "abort" in str(ex)

    def test_inheritance(self):
        assert issubclass(VMAbortException, VMException)
        assert issubclass(VMAbortException, NeoException)


class TestCryptoException:
    """Tests for CryptoException."""

    def test_basic(self):
        ex = CryptoException("missing library")
        assert "missing library" in str(ex)

    def test_inheritance(self):
        """CryptoException inherits NeoException, NOT VMException."""
        assert issubclass(CryptoException, NeoException)
        assert not issubclass(CryptoException, VMException)
