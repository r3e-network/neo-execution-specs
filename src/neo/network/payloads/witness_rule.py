"""
WitnessRule - Represents a witness rule.

Reference: Neo.Network.P2P.Payloads.WitnessRule
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter
    from neo.network.payloads.witness_condition import WitnessCondition

class WitnessRuleAction(IntEnum):
    """Action for a witness rule."""
    DENY = 0
    ALLOW = 1

@dataclass
class WitnessRule:
    """Represents a witness rule."""
    
    action: WitnessRuleAction = WitnessRuleAction.DENY
    condition: "WitnessCondition" | None = None
    
    @property
    def size(self) -> int:
        """Get the serialized size."""
        return 1 + (self.condition.size if self.condition else 1)
    
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the rule."""
        writer.write_byte(int(self.action))
        if self.condition:
            self.condition.serialize(writer)
    
    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "WitnessRule":
        """Deserialize a rule."""
        from neo.network.payloads.witness_condition import WitnessCondition
        action = WitnessRuleAction(reader.read_byte())
        condition = WitnessCondition.deserialize(reader)
        return cls(action=action, condition=condition)
