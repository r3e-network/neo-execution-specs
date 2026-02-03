"""Neo N3 Ping Payload."""

from dataclasses import dataclass


@dataclass
class PingPayload:
    """Ping/Pong payload."""
    last_block_index: int
    timestamp: int
    nonce: int
