"""ContractManifest - Manifest definition for contracts."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from .contract_abi import ContractAbi
from .contract_group import ContractGroup
from .contract_permission import ContractPermission

@dataclass
class ContractManifest:
    """Represents the manifest of a smart contract."""
    
    MAX_LENGTH = 65535  # ushort.MaxValue
    
    name: str = ""
    groups: list[ContractGroup] = field(default_factory=list)
    supported_standards: list[str] = field(default_factory=list)
    abi: ContractAbi = field(default_factory=ContractAbi)
    permissions: list[ContractPermission] = field(default_factory=list)
    trusts: list[bytes] = field(default_factory=list)  # Empty = wildcard
    extra: dict[str, Any] | None = None
    
    def to_json(self) -> dict[str, Any]:
        """Convert to JSON object."""
        return {
            "name": self.name,
            "groups": [g.to_json() for g in self.groups],
            "features": {},
            "supportedstandards": self.supported_standards,
            "abi": self.abi.to_json(),
            "permissions": [p.to_json() for p in self.permissions],
            "trusts": "*" if not self.trusts else [t.hex() for t in self.trusts],
            "extra": self.extra
        }
    
    @classmethod
    def from_json(cls, json: dict[str, Any]) -> ContractManifest:
        """Create from JSON object."""
        trusts_val = json.get("trusts", "*")
        return cls(
            name=json.get("name", ""),
            groups=[ContractGroup.from_json(g) for g in json.get("groups", [])],
            supported_standards=json.get("supportedstandards", []),
            abi=ContractAbi.from_json(json.get("abi", {})),
            permissions=[ContractPermission.from_json(p) for p in json.get("permissions", [])],
            trusts=[] if trusts_val == "*" else [bytes.fromhex(t) for t in trusts_val],
            extra=json.get("extra")
        )
