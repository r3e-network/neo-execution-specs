"""ContractPermission - Permission definition for contracts."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ContractPermission:
    """Represents a permission of a contract."""
    
    # Contract hash or group pubkey (None = wildcard)
    contract: Optional[bytes] = None
    # Allowed methods (empty list = wildcard)
    methods: List[str] = field(default_factory=list)
    
    def is_allowed(self, target_contract: Any, method: str) -> bool:
        """Check if calling the method is allowed."""
        # Wildcard contract
        if self.contract is None:
            pass
        elif hasattr(target_contract, 'hash'):
            if self.contract != target_contract.hash.data:
                return False
        
        # Wildcard methods
        if not self.methods:
            return True
        return method in self.methods
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON object."""
        return {
            "contract": "*" if self.contract is None else self.contract.hex(),
            "methods": "*" if not self.methods else self.methods
        }
    
    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> ContractPermission:
        """Create from JSON object."""
        contract_val = json.get("contract", "*")
        methods_val = json.get("methods", "*")
        
        return cls(
            contract=None if contract_val == "*" else bytes.fromhex(contract_val),
            methods=[] if methods_val == "*" else methods_val
        )
