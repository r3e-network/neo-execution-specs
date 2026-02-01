"""ContractParameterDefinition - Parameter definition for methods."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from neo.smartcontract.contract_parameter_type import ContractParameterType


@dataclass
class ContractParameterDefinition:
    """Represents a parameter of a contract method or event."""
    
    name: str = ""
    type: ContractParameterType = ContractParameterType.ANY
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON object."""
        return {
            "name": self.name,
            "type": self.type.name.lower()
        }
    
    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> ContractParameterDefinition:
        """Create from JSON object."""
        type_str = json.get("type", "any").upper()
        return cls(
            name=json.get("name", ""),
            type=ContractParameterType[type_str]
        )
