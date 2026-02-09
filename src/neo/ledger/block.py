"""Neo N3 Block implementation."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from neo.network.payloads.header import Header

if TYPE_CHECKING:
    from neo.network.payloads.transaction import Transaction

# Backward-compatible alias
BlockHeader = Header


@dataclass
class Block:
    """Neo N3 Block."""
    header: Header
    transactions: List["Transaction"] = field(default_factory=list)

    @property
    def hash(self) -> bytes:
        return self.header.hash

    @property
    def index(self) -> int:
        return self.header.index

    @property
    def timestamp(self) -> int:
        return self.header.timestamp
