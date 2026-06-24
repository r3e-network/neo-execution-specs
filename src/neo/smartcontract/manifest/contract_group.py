"""ContractGroup - Group definition for contracts."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

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

        Mirrors C# ``ContractGroup.IsValid`` =
        ``Crypto.VerifySignature(hash.ToArray(), Signature, PubKey)``, where
        ``Crypto.VerifySignature`` calls ``ECDsa.VerifyData(..., SHA256)`` —
        i.e. it hashes the 20-byte contract hash with SHA-256 and verifies the
        signature over that digest. ``verify_signature`` here takes a SHA-256
        digest (it uses ``Prehashed``), so we must pass ``SHA256(hash.data)``;
        passing the raw 20-byte hash would verify over the wrong message and
        reject every C#-valid group signature.
        """
        if not self.pubkey or not self.signature:
            return False
        try:
            import hashlib

            digest = hashlib.sha256(hash.data).digest()
            return verify_signature(
                digest,
                self.signature,
                self.pubkey,
                SECP256R1,
            )
        except (ValueError, TypeError, OverflowError):
            return False
    
    def to_json(self) -> dict[str, Any]:
        """Convert to JSON object."""
        return {
            "pubkey": self.pubkey.hex(),
            "signature": self.signature.hex()
        }
    
    @classmethod
    def from_json(cls, json: dict[str, Any]) -> ContractGroup:
        """Create from JSON object."""
        group = cls(
            pubkey=bytes.fromhex(json.get("pubkey", "")),
            signature=bytes.fromhex(json.get("signature", ""))
        )
        # C# ContractGroup.FromJson rejects signatures whose length != 64.
        if len(group.signature) != 64:
            raise ValueError(
                f"Signature length({len(group.signature)}) is not 64"
            )
        return group
