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
        manifest = cls(
            name=json.get("name", ""),
            groups=[ContractGroup.from_json(g) for g in json.get("groups", [])],
            supported_standards=json.get("supportedstandards", []),
            abi=ContractAbi.from_json(json.get("abi", {})),
            permissions=[ContractPermission.from_json(p) for p in json.get("permissions", [])],
            trusts=[] if trusts_val == "*" else [bytes.fromhex(t) for t in trusts_val],
            extra=json.get("extra")
        )

        # C# ContractManifest.FromJson validation (v3.10.0).
        if not manifest.name:
            raise ValueError("Name in ContractManifest is empty")
        # Duplicate group public keys are rejected (ToDictionary(p => p.PubKey)).
        group_keys = [g.pubkey for g in manifest.groups]
        if len(set(group_keys)) != len(group_keys):
            raise ValueError("Duplicate group key in ContractManifest")
        # The features field must be present and empty.
        features = json.get("features")
        if not isinstance(features, dict) or len(features) != 0:
            raise ValueError("Features field must be empty")
        if any(not s for s in manifest.supported_standards):
            raise ValueError("SupportedStandards in ContractManifest has empty string")
        # Duplicate supported standards are rejected.
        if len(set(manifest.supported_standards)) != len(manifest.supported_standards):
            raise ValueError("Duplicate supported standard in ContractManifest")
        # Duplicate permission contracts are rejected.
        permission_contracts = [p.contract for p in manifest.permissions]
        if len(set(permission_contracts)) != len(permission_contracts):
            raise ValueError("Duplicate permission contract in ContractManifest")
        # Duplicate trusts are rejected.
        if len(set(manifest.trusts)) != len(manifest.trusts):
            raise ValueError("Duplicate trust in ContractManifest")
        return manifest

    def is_valid(self, limits: Any, hash: Any) -> bool:
        """C# ``ContractManifest.IsValid(limits, hash)`` (ContractManifest.cs:182).

        The manifest must be serializable within ``limits`` and every
        ``ContractGroup`` must carry a valid signature over the contract
        ``hash``. The serializable bound is enforced upstream by the
        ``MAX_LENGTH`` (<= MaxItemSize) check on the manifest bytes at deploy
        time, so this verifies that every group's signature is valid for the
        computed contract hash (``Groups.All(u => u.IsValid(hash))``).
        """
        return all(group.is_valid(hash) for group in self.groups)
