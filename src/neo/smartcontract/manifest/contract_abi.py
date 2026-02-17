"""ContractAbi - ABI definition for contracts."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from .contract_method_descriptor import ContractMethodDescriptor
from .contract_event_descriptor import ContractEventDescriptor

@dataclass
class ContractAbi:
    """Represents the ABI of a smart contract."""
    
    methods: list[ContractMethodDescriptor] = field(default_factory=list)
    events: list[ContractEventDescriptor] = field(default_factory=list)
    
    def get_method(self, name: str, pcount: int = -1) -> ContractMethodDescriptor | None:
        """Get method by name and parameter count.
        
        Args:
            name: Method name.
            pcount: Parameter count (-1 for any).
        """
        if pcount >= 0:
            for m in self.methods:
                if m.name == name and len(m.parameters) == pcount:
                    return m
            return None
        else:
            for m in self.methods:
                if m.name == name:
                    return m
            return None
    
    def to_json(self) -> dict[str, Any]:
        """Convert to JSON object."""
        return {
            "methods": [m.to_json() for m in self.methods],
            "events": [e.to_json() for e in self.events]
        }
    
    @classmethod
    def from_json(cls, json: dict[str, Any]) -> ContractAbi:
        """Create from JSON object."""
        return cls(
            methods=[
                ContractMethodDescriptor.from_json(m)
                for m in json.get("methods", [])
            ],
            events=[
                ContractEventDescriptor.from_json(e)
                for e in json.get("events", [])
            ]
        )
