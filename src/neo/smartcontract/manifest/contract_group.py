"""ContractGroup - Group definition for contracts."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from neo.types import UInt160
from neo.crypto.ecc.signature import verify_signature
from neo.crypto.ecc.curve import SECP256R1


@dataclass
class ContractGroup:
    """Represents a group of contracts."""
    
    pubkey: bytes = b""
    signature: bytes = b""
    
    def is_valid(self, hash: UInt160) -> bool:
        """Check if the group is valid for the given hash.
        
        Verifies that the signature is a valid ECDSA signature of the
        contract hash using the group's public key.
        """
        if not self.pubkey or not self.signature:
            return False
        try:
            # The message is the contract hash bytes
            message = hash.data
            return verify_signature(
                message, 
                self.signature, 
                self.pubkey,
                SECP256R1
            )
        except Exception:
            return False
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON object."""
        return {
            "pubkey": self.pubkey.hex(),
            "signature": self.signature.hex()
        }
    
    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> ContractGroup:
        """Create from JSON object."""
        return cls(
            pubkey=bytes.fromhex(json.get("pubkey", "")),
            signature=bytes.fromhex(json.get("signature", ""))
        )
