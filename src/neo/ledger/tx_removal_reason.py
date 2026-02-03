"""Neo N3 Transaction Removal Reason."""

from enum import IntEnum


class TransactionRemovalReason(IntEnum):
    """Reasons for tx removal."""
    ADDED_TO_BLOCK = 0
    EXPIRED = 1
    INVALID = 2
    POLICY_VIOLATION = 3
    UNKNOWN = 4
