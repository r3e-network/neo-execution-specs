"""
TransactionAttribute - Base class for transaction attributes.

Reference: Neo.Network.P2P.Payloads.TransactionAttribute
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.network.payloads.transaction import Transaction


class TransactionAttributeType(IntEnum):
    """Types of transaction attributes."""
    HIGH_PRIORITY = 0x01
    ORACLE_RESPONSE = 0x11
    NOT_VALID_BEFORE = 0x20
    CONFLICTS = 0x21
    NOTARY_ASSISTED = 0x22


@dataclass
class TransactionAttribute(ABC):
    """Base class for transaction attributes."""
    
    @property
    @abstractmethod
    def type(self) -> TransactionAttributeType:
        """Get the attribute type."""
        pass
    
    @property
    def allow_multiple(self) -> bool:
        """Whether multiple attributes of this type are allowed."""
        return False
