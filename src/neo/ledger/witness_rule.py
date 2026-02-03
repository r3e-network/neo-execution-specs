"""Neo N3 Witness Rule."""

from dataclasses import dataclass
from enum import IntEnum


class WitnessRuleAction(IntEnum):
    """Witness rule action."""
    DENY = 0
    ALLOW = 1


@dataclass
class WitnessRule:
    """Witness rule."""
    action: WitnessRuleAction
    condition: dict
