"""Neo N3 Oracle Response Attribute."""

from dataclasses import dataclass


@dataclass
class OracleResponse:
    """Oracle response attribute."""
    id: int
    code: int
    result: bytes
