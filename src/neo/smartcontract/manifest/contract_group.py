"""ContractGroup - Group definition for contracts."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from neo.types import UInt160


@dataclass
class ContractGroup:
    """Represents a group of contracts."""
    
    pubkey: bytes = b""
    signature: bytes = b""
    
    def is_valid(self, hash: UInt160) -> bool:
        """Check if the group is valid for the given hash."""
        # TODO: Implement signature verification
        return True
    
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
