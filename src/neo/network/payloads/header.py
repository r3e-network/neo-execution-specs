"""Neo N3 Header."""

from dataclasses import dataclass, field


@dataclass
class Header:
    """Block header."""
    version: int = 0
    prev_hash: bytes = field(default_factory=lambda: bytes(32))
    merkle_root: bytes = field(default_factory=lambda: bytes(32))
    timestamp: int = 0
    nonce: int = 0
    index: int = 0
    primary_index: int = 0
    next_consensus: bytes = field(default_factory=lambda: bytes(20))
