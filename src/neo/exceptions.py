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


class CatchableException(VMException):
    """A VM exception that can be caught by an in-script TRY/CATCH handler.

    Mirrors C# Neo.VM.CatchableException: only exceptions of this type are
    routed through ExecuteThrow (gated on Limits.CatchEngineExceptions). All
    other engine-internal errors (InvalidOperationException, type/cast errors,
    etc.) bypass the try-stack and FAULT immediately, matching C#'s
    `catch (CatchableException) when (...)` vs the outer `catch (Exception) ->
    OnFault`.
    """
    pass


class CryptoException(NeoException):
    """Cryptography library missing or misconfigured."""
    pass
