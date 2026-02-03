"""Neo N3 Oracle Response Code."""

from enum import IntEnum


class OracleResponseCode(IntEnum):
    """Oracle response codes."""
    SUCCESS = 0x00
    PROTOCOL_NOT_SUPPORTED = 0x10
    CONSENSUS_UNREACHABLE = 0x12
    NOT_FOUND = 0x14
    TIMEOUT = 0x16
    FORBIDDEN = 0x18
    RESPONSE_TOO_LARGE = 0x1a
    INSUFFICIENT_FUNDS = 0x1c
    CONTENT_TYPE_NOT_SUPPORTED = 0x1f
    ERROR = 0xff
