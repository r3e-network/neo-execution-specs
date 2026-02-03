"""Neo N3 Addr Payload."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class NetworkAddress:
    """Network address."""
    timestamp: int
    address: str
    port: int


@dataclass
class AddrPayload:
    """Address list payload."""
    addresses: List[NetworkAddress] = field(default_factory=list)
