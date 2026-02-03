"""Neo N3 NEP6 Wallet file."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class NEP6Wallet:
    """NEP6 wallet format."""
    name: str = ""
    version: str = "1.0"
    accounts: List = field(default_factory=list)
    extra: dict = field(default_factory=dict)
