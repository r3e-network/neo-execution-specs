"""Neo N3 Transaction Attribute."""

from enum import IntEnum


class TransactionAttributeType(IntEnum):
    """Attribute types."""
    HIGH_PRIORITY = 0x01
    ORACLE_RESPONSE = 0x11
    NOT_VALID_BEFORE = 0x20
    CONFLICTS = 0x21
    NOTARY_ASSISTED = 0x22
