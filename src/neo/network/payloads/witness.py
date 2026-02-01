"""
Witness - Contains verification and invocation scripts.

Reference: Neo.Network.P2P.Payloads.Witness
"""

from dataclasses import dataclass
from typing import Optional
from neo.crypto.hash import hash160


@dataclass
class Witness:
    """
    Represents a witness containing invocation and verification scripts.
    """
    
    invocation_script: bytes
    """The invocation script (contains signatures)."""
    
    verification_script: bytes
    """The verification script (contains public keys)."""
    
    @property
    def script_hash(self) -> bytes:
        """Get the script hash of the verification script."""
        return hash160(self.verification_script)
    
    @property
    def size(self) -> int:
        """Get the serialized size of the witness."""
        return (
            self._get_var_size(len(self.invocation_script)) +
            len(self.invocation_script) +
            self._get_var_size(len(self.verification_script)) +
            len(self.verification_script)
        )
    
    @staticmethod
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
