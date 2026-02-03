"""Neo N3 Version Payload."""

from dataclasses import dataclass


@dataclass
class VersionPayload:
    """Version message payload."""
    magic: int
    version: int
    timestamp: int
    nonce: int
    user_agent: str
    start_height: int
