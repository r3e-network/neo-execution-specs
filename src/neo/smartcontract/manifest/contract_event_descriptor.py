"""ContractEventDescriptor - Event descriptor for contracts."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List

from .contract_parameter_definition import ContractParameterDefinition


@dataclass
class ContractEventDescriptor:
    """Represents an event in a contract ABI."""
    
    name: str = ""
    parameters: List[ContractParameterDefinition] = field(default_factory=list)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON object."""
        return {
            "name": self.name,
            "parameters": [p.to_json() for p in self.parameters]
        }
    
    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> ContractEventDescriptor:
        """Create from JSON object."""
        return cls(
            name=json.get("name", ""),
            parameters=[
                ContractParameterDefinition.from_json(p)
                for p in json.get("parameters", [])
            ]
        )
