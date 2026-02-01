"""GAS Token native contract."""

from __future__ import annotations
from dataclasses import dataclass
from neo.types import UInt160


@dataclass
class GasToken:
    """GAS token - utility token."""
    
    id: int = -6
    name: str = "GasToken"
    symbol: str = "GAS"
    decimals: int = 8
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("d2a4cff31913016155e38e474a2c06d08be276cf")[::-1])
