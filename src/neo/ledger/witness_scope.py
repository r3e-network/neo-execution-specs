"""Neo N3 Witness Scope."""

from enum import IntFlag


class WitnessScope(IntFlag):
    """Witness scope flags."""
    NONE = 0
    CALLED_BY_ENTRY = 0x01
    CUSTOM_CONTRACTS = 0x10
    CUSTOM_GROUPS = 0x20
    WITNESS_RULES = 0x40
    GLOBAL = 0x80
