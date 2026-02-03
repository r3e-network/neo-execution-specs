"""Neo N3 Oracle Request."""

from dataclasses import dataclass


@dataclass
class OracleRequest:
    """Oracle request."""
    id: int
    original_tx: bytes
    gas_for_response: int
    url: str
    filter: str
    callback: str
    user_data: bytes
