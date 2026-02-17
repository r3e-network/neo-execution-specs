"""Neo N3 GetData Payload."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class GetDataPayload:
    """GetData request."""
    type: int
    hashes: list[bytes] = field(default_factory=list)
