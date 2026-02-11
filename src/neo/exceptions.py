"""Neo exceptions."""


class NeoException(Exception):
    """Base exception for Neo."""
    pass


class VMException(NeoException):
    """VM execution exception."""
    pass


class InvalidOperationException(VMException):
    """Invalid operation."""
    pass


class OutOfGasException(VMException):
    """Out of gas."""
    pass


class StackOverflowException(VMException):
    """Stack overflow."""
    pass


class VMAbortException(VMException):
    """Uncatchable VM abort — bypasses try/catch routing."""
    pass


class CryptoException(NeoException):
    """Cryptography library missing or misconfigured."""
    pass
