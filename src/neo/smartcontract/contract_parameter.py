"""Neo N3 Contract Parameter."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ContractParameter:
    """Contract parameter."""
    type: int
    value: Any = None
