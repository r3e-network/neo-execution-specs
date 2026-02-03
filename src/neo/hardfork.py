"""Neo N3 Hardfork definitions."""

from enum import IntEnum


class Hardfork(IntEnum):
    """Protocol hardforks."""
    HF_ASPIDOCHELONE = 0
    HF_BASILISK = 1
    HF_COCKATRICE = 2
    HF_DOMOVOI = 3
