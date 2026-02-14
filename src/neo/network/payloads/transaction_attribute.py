"""
TransactionAttribute - Base class for transaction attributes.

Reference: Neo.Network.P2P.Payloads.TransactionAttribute
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


class TransactionAttributeType(IntEnum):
    """Types of transaction attributes."""
    HIGH_PRIORITY = 0x01
    ORACLE_RESPONSE = 0x11
    NOT_VALID_BEFORE = 0x20
    CONFLICTS = 0x21
    NOTARY_ASSISTED = 0x22


@dataclass
class TransactionAttribute(ABC):
    """Base class for transaction attributes."""
    
    @property
    @abstractmethod
    def type(self) -> TransactionAttributeType:
        pass
    
    @property
    def allow_multiple(self) -> bool:
        return False
    
    @property
    def size(self) -> int:
        return 1  # type byte
    
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the attribute."""
        writer.write_byte(int(self.type))
        self._serialize_without_type(writer)
    
    @abstractmethod
    def _serialize_without_type(self, writer: "BinaryWriter") -> None:
        """Serialize attribute data (without type byte)."""
        pass
    
    @staticmethod
    def deserialize(reader: "BinaryReader") -> "TransactionAttribute":
        """Deserialize an attribute."""
        attr_type = TransactionAttributeType(reader.read_byte())
        if attr_type == TransactionAttributeType.HIGH_PRIORITY:
            return HighPriorityAttribute()
        elif attr_type == TransactionAttributeType.NOT_VALID_BEFORE:
            return NotValidBeforeAttribute.deserialize_body(reader)
        elif attr_type == TransactionAttributeType.CONFLICTS:
            return ConflictsAttribute.deserialize_body(reader)
        elif attr_type == TransactionAttributeType.ORACLE_RESPONSE:
            return OracleResponseAttribute.deserialize_body(reader)
        elif attr_type == TransactionAttributeType.NOTARY_ASSISTED:
            return NotaryAssistedAttribute.deserialize_body(reader)
        else:
            raise ValueError(f"Unknown attribute type: {attr_type}")


@dataclass
class HighPriorityAttribute(TransactionAttribute):
    """High priority transaction attribute."""
    
    @property
    def type(self) -> TransactionAttributeType:
        return TransactionAttributeType.HIGH_PRIORITY
    
    def _serialize_without_type(self, writer: "BinaryWriter") -> None:
        pass  # No additional data


@dataclass
class NotValidBeforeAttribute(TransactionAttribute):
    """Not valid before attribute."""
    height: int = 0
    
    @property
    def type(self) -> TransactionAttributeType:
        return TransactionAttributeType.NOT_VALID_BEFORE
    
    @property
    def size(self) -> int:
        return 1 + 4  # type + height
    
    def _serialize_without_type(self, writer: "BinaryWriter") -> None:
        writer.write_uint32(self.height)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "NotValidBeforeAttribute":
        return NotValidBeforeAttribute(height=reader.read_uint32())


@dataclass
class ConflictsAttribute(TransactionAttribute):
    """Conflicts attribute."""
    hash: bytes = b""
    
    @property
    def type(self) -> TransactionAttributeType:
        return TransactionAttributeType.CONFLICTS
    
    @property
    def allow_multiple(self) -> bool:
        return True
    
    @property
    def size(self) -> int:
        return 1 + 32  # type + hash
    
    def _serialize_without_type(self, writer: "BinaryWriter") -> None:
        writer.write_bytes(self.hash)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "ConflictsAttribute":
        return ConflictsAttribute(hash=reader.read_bytes(32))


class OracleResponseCode(IntEnum):
    """Oracle response codes."""
    SUCCESS = 0x00
    PROTOCOL_NOT_SUPPORTED = 0x10
    CONSENSUS_UNREACHABLE = 0x12
    NOT_FOUND = 0x14
    TIMEOUT = 0x16
    FORBIDDEN = 0x18
    RESPONSE_TOO_LARGE = 0x1a
    INSUFFICIENT_FUNDS = 0x1c
    CONTENT_TYPE_NOT_SUPPORTED = 0x1f
    ERROR = 0xff


MAX_RESULT_SIZE = 0xFFFF


@dataclass
class OracleResponseAttribute(TransactionAttribute):
    """Oracle response attribute."""
    id: int = 0
    code: OracleResponseCode = OracleResponseCode.SUCCESS
    result: bytes = b""
    
    @property
    def type(self) -> TransactionAttributeType:
        return TransactionAttributeType.ORACLE_RESPONSE
    
    @property
    def size(self) -> int:
        from neo.network.payloads.witness import _get_var_size
        return 1 + 8 + 1 + _get_var_size(len(self.result)) + len(self.result)
    
    def _serialize_without_type(self, writer: "BinaryWriter") -> None:
        writer.write_uint64(self.id)
        writer.write_byte(int(self.code))
        writer.write_var_bytes(self.result)
    
    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "OracleResponseAttribute":
        id = reader.read_uint64()
        code = OracleResponseCode(reader.read_byte())
        result = reader.read_var_bytes(MAX_RESULT_SIZE)
        if code != OracleResponseCode.SUCCESS and len(result) > 0:
            raise ValueError("Result must be empty for non-success")
        return OracleResponseAttribute(id=id, code=code, result=result)


@dataclass
class NotaryAssistedAttribute(TransactionAttribute):
    """Notary assisted transaction attribute."""
    nkeys: int = 0

    @property
    def type(self) -> TransactionAttributeType:
        return TransactionAttributeType.NOTARY_ASSISTED

    @property
    def size(self) -> int:
        return 1 + 1  # type + nkeys

    def _serialize_without_type(self, writer: "BinaryWriter") -> None:
        writer.write_byte(self.nkeys)

    @staticmethod
    def deserialize_body(reader: "BinaryReader") -> "NotaryAssistedAttribute":
        return NotaryAssistedAttribute(nkeys=reader.read_byte())
