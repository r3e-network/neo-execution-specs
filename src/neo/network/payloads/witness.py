"""Neo N3 Witness.

Reference: Neo.Network.P2P.Payloads.Witness
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


def _get_var_size(value: int) -> int:
    """Get variable int size."""
    if value < 0xFD:
        return 1
    elif value <= 0xFFFF:
        return 3
    elif value <= 0xFFFFFFFF:
        return 5
    return 9


@dataclass
class Witness:
    """Transaction witness containing invocation and verification scripts."""
    invocation_script: bytes = b""
    verification_script: bytes = b""
    
    @classmethod
    def empty(cls) -> "Witness":
        """Create empty witness."""
        return cls()
    
    @property
    def size(self) -> int:
        """Get serialized size."""
        return (_get_var_size(len(self.invocation_script)) + 
                len(self.invocation_script) +
                _get_var_size(len(self.verification_script)) + 
                len(self.verification_script))
    
    @property
    def script_hash(self) -> bytes:
        """Get verification script hash."""
        from neo.crypto.hash import hash160
        return hash160(self.verification_script)
    
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the witness."""
        writer.write_var_bytes(self.invocation_script)
        writer.write_var_bytes(self.verification_script)
    
    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Witness":
        """Deserialize a witness."""
        invocation = reader.read_var_bytes(0xFFFF)
        verification = reader.read_var_bytes(0xFFFF)
        return cls(invocation_script=invocation, verification_script=verification)
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        from neo.io.binary_writer import BinaryWriter
        writer = BinaryWriter()
        self.serialize(writer)
        return writer.to_bytes()
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Witness":
        """Deserialize from bytes."""
        from neo.io.binary_reader import BinaryReader
        reader = BinaryReader(data)
        return cls.deserialize(reader)
