"""Neo N3 Signer Scope."""

from enum import IntFlag


class WitnessScope(IntFlag):
    """Witness scope."""
    NONE = 0
    CALLED_BY_ENTRY = 1
    CUSTOM_CONTRACTS = 16
    CUSTOM_GROUPS = 32
    WITNESS_RULES = 64
    GLOBAL = 128
