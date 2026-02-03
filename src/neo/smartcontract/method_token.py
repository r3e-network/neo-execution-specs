"""Neo N3 Method Token."""

from dataclasses import dataclass


@dataclass
class MethodToken:
    """Method token for calls."""
    hash: bytes
    method: str
    params_count: int
    has_return: bool
    call_flags: int
