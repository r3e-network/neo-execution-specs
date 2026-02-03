"""Neo N3 Extensible Payload."""

from dataclasses import dataclass


@dataclass
class ExtensiblePayload:
    """Extensible payload."""
    category: str
    valid_block_start: int
    valid_block_end: int
    sender: bytes
    data: bytes
    witness: object = None
