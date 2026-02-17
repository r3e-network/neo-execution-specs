"""ContractMethodDescriptor - Method descriptor for contracts."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from neo.smartcontract.contract_parameter_type import ContractParameterType
from .contract_parameter_definition import ContractParameterDefinition

@dataclass
class ContractMethodDescriptor:
    """Represents a method in a contract ABI."""
    
    name: str = ""
    parameters: list[ContractParameterDefinition] = field(default_factory=list)
    return_type: ContractParameterType = ContractParameterType.VOID
    offset: int = 0
    safe: bool = False
    
    def to_json(self) -> dict[str, Any]:
        """Convert to JSON object."""
        return {
            "name": self.name,
            "parameters": [p.to_json() for p in self.parameters],
            "returntype": self.return_type.name.lower(),
            "offset": self.offset,
            "safe": self.safe
        }
    
    @classmethod
    def from_json(cls, json: dict[str, Any]) -> ContractMethodDescriptor:
        """Create from JSON object."""
        return_type_str = json.get("returntype", "void").upper()
        return cls(
            name=json.get("name", ""),
            parameters=[
                ContractParameterDefinition.from_json(p) 
                for p in json.get("parameters", [])
            ],
            return_type=ContractParameterType[return_type_str],
            offset=json.get("offset", 0),
            safe=json.get("safe", False)
        )
