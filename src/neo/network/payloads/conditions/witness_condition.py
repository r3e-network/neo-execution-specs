"""Neo N3 Witness Condition."""

from dataclasses import dataclass
from enum import IntEnum


class WitnessConditionType(IntEnum):
    """Condition types."""
    BOOLEAN = 0x00
    NOT = 0x01
    AND = 0x02
    OR = 0x03
    SCRIPT_HASH = 0x18
    GROUP = 0x19
    CALLED_BY_ENTRY = 0x20
    CALLED_BY_CONTRACT = 0x28
    CALLED_BY_GROUP = 0x29
