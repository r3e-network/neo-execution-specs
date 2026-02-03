"""Neo N3 Role type."""

from enum import IntEnum


class Role(IntEnum):
    """Node roles."""
    STATE_VALIDATOR = 4
    ORACLE = 8
    NEO_FS_ALPHABET_NODE = 16
    P2P_NOTARY = 32
