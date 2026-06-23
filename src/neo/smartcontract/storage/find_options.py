"""Neo N3 Find Options."""

from enum import IntFlag


class FindOptions(IntFlag):
    """Storage find options."""
    NONE = 0
    KEYS_ONLY = 1
    REMOVE_PREFIX = 2
    VALUES_ONLY = 4
    DESERIALIZE_VALUES = 8
    PICK_FIELD0 = 16
    PICK_FIELD1 = 32
    BACKWARDS = 128
    # All valid flags combined (C# FindOptions.All = 191).
    ALL_MASK = KEYS_ONLY | REMOVE_PREFIX | VALUES_ONLY | DESERIALIZE_VALUES | PICK_FIELD0 | PICK_FIELD1 | BACKWARDS
