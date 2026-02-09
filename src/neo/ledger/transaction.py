"""Neo N3 Transaction implementation."""

from dataclasses import dataclass, field
from typing import List
from enum import IntEnum


class TransactionAttributeType(IntEnum):
    """Transaction attribute types."""
    HIGH_PRIORITY = 0x01
    ORACLE_RESPONSE = 0x11
    NOT_VALID_BEFORE = 0x20
    CONFLICTS = 0x21
    NOTARY_ASSISTED = 0x22


@dataclass
class TransactionAttribute:
    """Transaction attribute."""
    type: TransactionAttributeType
    data: bytes = b""


@dataclass
class Signer:
    """Transaction signer."""
    account: bytes  # UInt160
    scopes: int = 1  # CalledByEntry
    allowed_contracts: List[bytes] = field(default_factory=list)
    allowed_groups: List[bytes] = field(default_factory=list)
    rules: List = field(default_factory=list)


@dataclass
class Witness:
    """Transaction witness."""
    invocation: bytes = b""
    verification: bytes = b""
