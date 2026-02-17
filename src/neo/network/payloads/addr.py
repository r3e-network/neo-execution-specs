"""Neo N3 Addr Payload."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class NetworkAddress:
    """Network address."""
    timestamp: int
    address: str
    port: int

@dataclass
class AddrPayload:
    """Address list payload."""
    addresses: list[NetworkAddress] = field(default_factory=list)
