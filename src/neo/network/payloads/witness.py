"""
Witness - Contains verification and invocation scripts.

Reference: Neo.Network.P2P.Payloads.Witness
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


# Maximum script sizes (from C# reference)
MAX_INVOCATION_SCRIPT = 1024
MAX_VERIFICATION_SCRIPT = 1024


@dataclass
class Witness:
    """
    Represents a witness containing invocation and verification scripts.
    """
    
    invocation_script: bytes = b""
    """The invocation script (contains signatures)."""
    
    verification_script: bytes = b""
    """The verification script (contains public keys)."""
    
    _script_hash: bytes | None = None
    
    @property
    def script_hash(self) -> bytes:
        """Get the script hash of the verification script."""
        if self._script_hash is None:
            from neo.crypto.hash import hash160
            self._script_hash = hash160(self.verification_script)
        return self._script_hash
    
    @property
    def size(self) -> int:
        """Get the serialized size of the witness."""
        return (
            _get_var_size(len(self.invocation_script)) +
            len(self.invocation_script) +
            _get_var_size(len(self.verification_script)) +
            len(self.verification_script)
        )
    
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the witness."""
        writer.write_var_bytes(self.invocation_script)
        writer.write_var_bytes(self.verification_script)
    
    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Witness":
        """Deserialize a witness."""
        invocation = reader.read_var_bytes(MAX_INVOCATION_SCRIPT)
        verification = reader.read_var_bytes(MAX_VERIFICATION_SCRIPT)
        return cls(
            invocation_script=invocation,
            verification_script=verification
        )
    
    @classmethod
    def empty(cls) -> "Witness":
        """Create an empty witness."""
        return cls(invocation_script=b"", verification_script=b"")


def _get_var_size(value: int) -> int:
    """Get the size of a variable-length integer."""
    if value < 0xFD:
        return 1
    elif value <= 0xFFFF:
        return 3
    elif value <= 0xFFFFFFFF:
        return 5
    else:
        return 9
