"""ContractState - Deployed contract state."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from neo.types import UInt160
from neo.smartcontract.nef_file import NefFile
from neo.smartcontract.manifest import ContractManifest


@dataclass
class ContractState:
    """Represents a deployed contract."""
    
    id: int = 0
    update_counter: int = 0
    hash: UInt160 = None
    nef: NefFile = None
    manifest: ContractManifest = None
    
    def __post_init__(self):
        if self.hash is None:
            self.hash = UInt160.ZERO
        if self.nef is None:
            self.nef = NefFile()
        if self.manifest is None:
            self.manifest = ContractManifest()
    
    @property
    def script(self) -> bytes:
        """Get the contract script."""
        return self.nef.script
    
    def can_call(self, target: ContractState, method: str) -> bool:
        """Check if this contract can call target method."""
        for perm in self.manifest.permissions:
            if perm.is_allowed(target, method):
                return True
        return False
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON."""
        return {
            "id": self.id,
            "updatecounter": self.update_counter,
            "hash": str(self.hash),
            "nef": self.nef.to_json(),
            "manifest": self.manifest.to_json()
        }
