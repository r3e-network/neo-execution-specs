"""Neo N3 NEP6 Wallet file."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class NEP6Wallet:
    """NEP6 wallet format."""
    name: str = ""
    version: str = "1.0"
    accounts: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)
