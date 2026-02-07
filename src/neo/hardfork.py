"""Neo N3 Hardfork definitions."""

from enum import IntEnum


class Hardfork(IntEnum):
    """Protocol hardforks in Neo ordering."""

    HF_ASPIDOCHELONE = 0
    HF_BASILISK = 1
    HF_COCKATRICE = 2
    HF_DOMOVOI = 3
    HF_ECHIDNA = 4
    HF_FAUN = 5
    HF_GORGON = 6
