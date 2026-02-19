"""
WitnessCondition - Represents witness conditions.

Reference: Neo.Network.P2P.Payloads.Conditions
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter

MAX_NESTING_DEPTH = 2
MAX_SUBITEMS = 16

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
    def serialize(self, writer: BinaryWriter) -> None:
        pass
    
    @staticmethod
    def deserialize(reader: BinaryReader, depth: int = 0) -> WitnessCondition:
        """Deserialize a condition."""
        if depth > MAX_NESTING_DEPTH:
            raise ValueError(
                f"WitnessCondition nesting depth exceeds {MAX_NESTING_DEPTH}"
            )
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
            return NotCondition.deserialize_body(reader, depth)
        elif ctype == WitnessConditionType.AND:
            return AndCondition.deserialize_body(reader, depth)
        elif ctype == WitnessConditionType.OR:
            return OrCondition.deserialize_body(reader, depth)
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
    
    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        writer.write_bool(self.expression)
    
    @staticmethod
    def deserialize_body(reader: BinaryReader) -> BooleanCondition:
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
    
    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))

@dataclass
class ScriptHashCondition(WitnessCondition):
    """Script hash condition."""

    hash: bytes = b""
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.SCRIPT_HASH
    
    @property
    def size(self) -> int:
        return 1 + 20
    
    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        writer.write_bytes(self.hash)
    
    @staticmethod
    def deserialize_body(reader: BinaryReader) -> ScriptHashCondition:
        return ScriptHashCondition(hash=reader.read_bytes(20))

@dataclass
class GroupCondition(WitnessCondition):
    """Group condition (EC point)."""

    group: bytes = b""
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.GROUP
    
    @property
    def size(self) -> int:
        return (1 + len(self.group)) if self.group else 1

    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        writer.write_ec_point(self.group)

    @staticmethod
    def deserialize_body(reader: BinaryReader) -> GroupCondition:
        return GroupCondition(group=reader.read_ec_point())

@dataclass
class CalledByContractCondition(WitnessCondition):
    """Called by contract condition."""

    hash: bytes = b""

    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.CALLED_BY_CONTRACT

    @property
    def size(self) -> int:
        return 1 + 20

    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        writer.write_bytes(self.hash)

    @staticmethod
    def deserialize_body(reader: BinaryReader) -> CalledByContractCondition:
        return CalledByContractCondition(hash=reader.read_bytes(20))

@dataclass
class CalledByGroupCondition(WitnessCondition):
    """Called by group condition."""

    group: bytes = b""

    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.CALLED_BY_GROUP

    @property
    def size(self) -> int:
        return (1 + len(self.group)) if self.group else 1
    
    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        writer.write_ec_point(self.group)
    
    @staticmethod
    def deserialize_body(reader: BinaryReader) -> CalledByGroupCondition:
        return CalledByGroupCondition(group=reader.read_ec_point())

@dataclass
class NotCondition(WitnessCondition):
    """Not condition."""

    expression: WitnessCondition | None = None
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.NOT
    
    @property
    def size(self) -> int:
        return 1 + (self.expression.size if self.expression else 0)
    
    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        if self.expression:
            self.expression.serialize(writer)
    
    @staticmethod
    def deserialize_body(reader: BinaryReader, depth: int = 0) -> NotCondition:
        expr = WitnessCondition.deserialize(reader, depth + 1)
        return NotCondition(expression=expr)

@dataclass
class AndCondition(WitnessCondition):
    """And condition."""

    expressions: list[WitnessCondition] = field(default_factory=list)
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.AND
    
    @property
    def size(self) -> int:
        from neo.network.payloads.witness import _get_var_size
        base = 1 + _get_var_size(len(self.expressions) if self.expressions else 0)
        return base + sum(e.size for e in (self.expressions or []))
    
    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        writer.write_var_int(len(self.expressions) if self.expressions else 0)
        for expr in (self.expressions or []):
            expr.serialize(writer)
    
    @staticmethod
    def deserialize_body(reader: BinaryReader, depth: int = 0) -> AndCondition:
        count = reader.read_var_int(MAX_SUBITEMS)
        if count < 2:
            raise ValueError("And condition requires at least 2 sub-expressions")
        exprs = [WitnessCondition.deserialize(reader, depth + 1) for _ in range(count)]
        return AndCondition(expressions=exprs)

@dataclass
class OrCondition(WitnessCondition):
    """Or condition."""

    expressions: list[WitnessCondition] = field(default_factory=list)
    
    @property
    def type(self) -> WitnessConditionType:
        return WitnessConditionType.OR
    
    @property
    def size(self) -> int:
        from neo.network.payloads.witness import _get_var_size
        base = 1 + _get_var_size(len(self.expressions) if self.expressions else 0)
        return base + sum(e.size for e in (self.expressions or []))
    
    def serialize(self, writer: BinaryWriter) -> None:
        writer.write_byte(int(self.type))
        writer.write_var_int(len(self.expressions) if self.expressions else 0)
        for expr in (self.expressions or []):
            expr.serialize(writer)
    
    @staticmethod
    def deserialize_body(reader: BinaryReader, depth: int = 0) -> OrCondition:
        count = reader.read_var_int(MAX_SUBITEMS)
        if count < 2:
            raise ValueError("Or condition requires at least 2 sub-expressions")
        exprs = [WitnessCondition.deserialize(reader, depth + 1) for _ in range(count)]
        return OrCondition(expressions=exprs)
