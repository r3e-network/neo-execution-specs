"""Neo N3 NEP6 Wallet."""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class NEP6Account:
    """NEP6 account."""
    address: str
    label: str = ""
    is_default: bool = False
    lock: bool = False
    key: str | None = None
