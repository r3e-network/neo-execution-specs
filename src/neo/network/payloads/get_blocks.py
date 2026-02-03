"""Neo N3 GetBlocks Payload."""

from dataclasses import dataclass


@dataclass
class GetBlocksPayload:
    """GetBlocks request."""
    hash_start: bytes
    count: int = -1
