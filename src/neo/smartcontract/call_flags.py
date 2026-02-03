"""Neo N3 Call Flags for contract invocation."""

from enum import IntFlag


class CallFlags(IntFlag):
    """Call flags for contract method invocation."""
    NONE = 0
    READ_STATES = 0b00000001
    WRITE_STATES = 0b00000010
    ALLOW_CALL = 0b00000100
    ALLOW_NOTIFY = 0b00001000
    STATES = READ_STATES | WRITE_STATES
    READ_ONLY = READ_STATES | ALLOW_CALL
    ALL = STATES | ALLOW_CALL | ALLOW_NOTIFY
