"""Neo N3 Oracle Request.

The canonical :class:`OracleRequest` IInteroperable lives in
``neo.native.oracle`` and mirrors C# ``OracleRequest`` (OracleRequest.cs).
This module re-exports it for backward compatibility so callers importing
``neo.native.oracle_request`` get the same type used by the Oracle contract.
"""

from neo.native.oracle import OracleRequest

__all__ = ["OracleRequest"]
