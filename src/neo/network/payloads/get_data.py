"""Neo N3 GetData Payload."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class GetDataPayload:
    """GetData request."""
    type: int
    hashes: List[bytes] = field(default_factory=list)
