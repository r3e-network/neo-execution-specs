"""Neo N3 Inv Payload."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class InvPayload:
    """Inventory payload."""
    type: int
    hashes: List[bytes] = field(default_factory=list)
