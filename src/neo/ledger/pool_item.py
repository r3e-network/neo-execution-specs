"""
PoolItem - Memory pool item wrapper.

Reference: Neo.Ledger.PoolItem
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.network.payloads.transaction import Transaction


@dataclass
class PoolItem:
    """Represents an item in the Memory Pool."""
    
    tx: "Transaction"
    """The transaction."""
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """Timestamp when transaction was stored."""
    
    last_broadcast: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """Timestamp when last broadcast to other nodes."""
