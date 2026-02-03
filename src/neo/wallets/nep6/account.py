"""Neo N3 NEP6 Wallet."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NEP6Account:
    """NEP6 account."""
    address: str
    label: str = ""
    is_default: bool = False
    lock: bool = False
    key: Optional[str] = None
