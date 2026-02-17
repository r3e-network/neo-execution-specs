"""Neo N3 Inv Payload."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class InvPayload:
    """Inventory payload."""
    type: int
    hashes: list[bytes] = field(default_factory=list)
