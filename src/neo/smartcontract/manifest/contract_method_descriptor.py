"""ContractMethodDescriptor - Method descriptor for contracts."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from neo.smartcontract.contract_parameter_type import ContractParameterType
from .contract_parameter_definition import (
    ContractParameterDefinition,
    PARAMETER_NAME_TO_TYPE,
    PARAMETER_TYPE_TO_NAME,
)

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
            "returntype": PARAMETER_TYPE_TO_NAME[self.return_type],
            "offset": self.offset,
            "safe": self.safe
        }
    
    @classmethod
    def from_json(cls, json: dict[str, Any]) -> ContractMethodDescriptor:
        """Create from JSON object."""
        return_type_str = json["returntype"] if "returntype" in json else "Void"
        if return_type_str not in PARAMETER_NAME_TO_TYPE:
            raise ValueError(f"Type({return_type_str}) in ContractMethodDescriptor is not valid")
        return cls(
            name=json.get("name", ""),
            parameters=[
                ContractParameterDefinition.from_json(p)
                for p in json.get("parameters", [])
            ],
            return_type=PARAMETER_NAME_TO_TYPE[return_type_str],
            offset=json.get("offset", 0),
            safe=json.get("safe", False)
        )
