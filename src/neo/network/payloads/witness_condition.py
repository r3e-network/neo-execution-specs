"""
WitnessCondition - Represents witness conditions.

Reference: Neo.Network.P2P.Payloads.Conditions
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


class WitnessConditionType(IntEnum):
    """Types of witness conditions."""
    BOOLEAN = 0x00
    NOT = 0x01
    AND = 0x02
    OR = 0x03
    SCRIPT_HASH = 0x18
    GROUP = 0x19
    CALLED_BY_ENTRY = 0x20
    CALLED_BY_CONTRACT = 0x28
    CALLED_BY_GROUP = 0x29


@dataclass
class WitnessCondition(ABC):
    """Base class for witness conditions."""
    
    @property
    @abstractmethod
    def type(self) -> WitnessConditionType:
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        pass
    
    @abstractmethod
    def serialize(self, writer: "BinaryWriter") -> None:
        pass
    
    @staticmethod
    def deserialize(reader: "BinaryReader") -> "WitnessCondition":
        """Deserialize a condition."""
        ctype = WitnessConditionType(reader.read_byte())
        if ctype == WitnessConditionType.BOOLEAN:
            return BooleanCondition.deserialize_body(reader)
        elif ctype == WitnessConditionType.CALLED_BY_ENTRY:
            return CalledByEntryCondition()
        elif ctype == WitnessConditionType.SCRIPT_HASH:
            return ScriptHashCondition.deserialize_body(reader)
        elif ctype == WitnessConditionType.GROUP:
            return GroupCondition.deserialize_body(reader)
        elif ctype == WitnessConditionType.CALLED_BY_CONTRACT:
            return CalledByContractCondition.deserialize_body(reader)
        elif ctype == WitnessConditionType.CALLED_BY_GROUP:
            return CalledByGroupCondition.deserialize_body(reader)
        elif ctype == WitnessConditionType.NOT:
            return NotCondition.deserialize_body(reader)
        elif ctype == WitnessConditionType.AND:
            return AndCondition.deserialize_body(reader)
        elif ctype == WitnessConditionType.OR:
            return OrCondition.deserialize_body(reader)
        else:
            raise ValueError(f"Unknown condition type: {ctype}")


@dataclass
class BooleanCondition(WitnessCondition):
    """Boolean condition."""
    expression: bool = True
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.BOOLEAN
    
    @property
    def size(self) -> int:
        return 2  # type + bool
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        writer.write_bool(self.expression)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "BooleanCondition":
        return BooleanCondition(expression=reader.read_bool())


@dataclass
class CalledByEntryCondition(WitnessCondition):
    """Called by entry condition."""
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.CALLED_BY_ENTRY
    
    @property
    def size(self) -> int:
        return 1
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))


@dataclass
class ScriptHashCondition(WitnessCondition):
    """Script hash condition."""
    hash: bytes = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.SCRIPT_HASH
    
    @property
    def size(self) -> int:
        return 1 + 20
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        writer.write_bytes(self.hash)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "ScriptHashCondition":
        return ScriptHashCondition(hash=reader.read_bytes(20))


@dataclass
class GroupCondition(WitnessCondition):
    """Group condition (EC point)."""
    group: bytes = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.GROUP
    
    @property
    def size(self) -> int:
        return 1 + len(self.group) if self.group else 1
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        writer.write_ec_point(self.group)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "GroupCondition":
        return GroupCondition(group=reader.read_ec_point())


@dataclass
class CalledByContractCondition(WitnessCondition):
    """Called by contract condition."""
    hash: bytes = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.CALLED_BY_CONTRACT
    
    @property
    def size(self) -> int:
        return 1 + 20
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        writer.write_bytes(self.hash)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "CalledByContractCondition":
        return CalledByContractCondition(hash=reader.read_bytes(20))


@dataclass
class CalledByGroupCondition(WitnessCondition):
    """Called by group condition."""
    group: bytes = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.CALLED_BY_GROUP
    
    @property
    def size(self) -> int:
        return 1 + len(self.group) if self.group else 1
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        writer.write_ec_point(self.group)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "CalledByGroupCondition":
        return CalledByGroupCondition(group=reader.read_ec_point())


@dataclass
class NotCondition(WitnessCondition):
    """Not condition."""
    expression: WitnessCondition = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.NOT
    
    @property
    def size(self) -> int:
        return 1 + (self.expression.size if self.expression else 0)
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        if self.expression:
            self.expression.serialize(writer)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "NotCondition":
        expr = WitnessCondition.deserialize(reader)
        return NotCondition(expression=expr)


@dataclass
class AndCondition(WitnessCondition):
    """And condition."""
    expressions: List[WitnessCondition] = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.AND
    
    @property
    def size(self) -> int:
        from neo.network.payloads.witness import _get_var_size
        base = 1 + _get_var_size(len(self.expressions) if self.expressions else 0)
        return base + sum(e.size for e in (self.expressions or []))
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        writer.write_var_int(len(self.expressions) if self.expressions else 0)
        for expr in (self.expressions or []):
            expr.serialize(writer)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "AndCondition":
        count = reader.read_var_int(16)
        exprs = [WitnessCondition.deserialize(reader) for _ in range(count)]
        return AndCondition(expressions=exprs)


@dataclass
class OrCondition(WitnessCondition):
    """Or condition."""
    expressions: List[WitnessCondition] = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.OR
    
    @property
    def size(self) -> int:
        from neo.network.payloads.witness import _get_var_size
        base = 1 + _get_var_size(len(self.expressions) if self.expressions else 0)
        return base + sum(e.size for e in (self.expressions or []))
    
    def serialize(self, writer: "BinaryWriter") -> None:
        writer.write_byte(int(self.type))
        writer.write_var_int(len(self.expressions) if self.expressions else 0)
        for expr in (self.expressions or []):
            expr.serialize(writer)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "OrCondition":
        count = reader.read_var_int(16)
        exprs = [WitnessCondition.deserialize(reader) for _ in range(count)]
        return OrCondition(expressions=exprs)
