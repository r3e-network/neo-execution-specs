"""Oracle response codes.

This module provides Oracle response codes used by the Oracle contract.
It is a re-export of the OracleResponseCode enum from oracle.py for
backward compatibility.
"""

from neo.native.oracle import OracleResponseCode

# Backward compatibility aliases
OracleResponseCode.SUCCESS = OracleResponseCode.Success  # type: ignore[attr-defined]
OracleResponseCode.PROTOCOL_NOT_SUPPORTED = OracleResponseCode.ProtocolNotSupported  # type: ignore[attr-defined]
OracleResponseCode.CONSENSUS_UNREACHABLE = OracleResponseCode.ConsensusUnreachable  # type: ignore[attr-defined]
OracleResponseCode.NOT_FOUND = OracleResponseCode.NotFound  # type: ignore[attr-defined]
OracleResponseCode.TIMEOUT = OracleResponseCode.Timeout  # type: ignore[attr-defined]
OracleResponseCode.FORBIDDEN = OracleResponseCode.Forbidden  # type: ignore[attr-defined]
OracleResponseCode.RESPONSE_TOO_LARGE = OracleResponseCode.ResponseTooLarge  # type: ignore[attr-defined]
OracleResponseCode.INSUFFICIENT_FUNDS = OracleResponseCode.InsufficientFunds  # type: ignore[attr-defined]
OracleResponseCode.CONTENT_TYPE_NOT_SUPPORTED = OracleResponseCode.ContentTypeNotSupported  # type: ignore[attr-defined]
OracleResponseCode.ERROR = OracleResponseCode.Error  # type: ignore[attr-defined]

__all__ = ["OracleResponseCode"]
