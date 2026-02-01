"""NEO Token native contract."""

from __future__ import annotations
from dataclasses import dataclass, field
from neo.types import UInt160


@dataclass
class NeoToken:
    """NEO token - governance token."""
    
    id: int = -5
    name: str = "NeoToken"
    symbol: str = "NEO"
    decimals: int = 0
    total_supply: int = 100_000_000
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("ef4073a0f2b305a38ec4050e4d3d28bc40ea63f5")[::-1])
