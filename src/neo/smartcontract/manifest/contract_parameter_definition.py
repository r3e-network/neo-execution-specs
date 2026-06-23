"""ContractParameterDefinition - Parameter definition for methods."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from neo.smartcontract.contract_parameter_type import ContractParameterType

# Exact C# PascalCase token names for ContractParameterType (Type.ToString() /
# Enum.Parse<ContractParameterType>). The Python enum uses SCREAMING_SNAKE_CASE
# names, so map both directions explicitly to stay byte-for-byte compatible.
PARAMETER_TYPE_TO_NAME: dict[ContractParameterType, str] = {
    ContractParameterType.ANY: "Any",
    ContractParameterType.BOOLEAN: "Boolean",
    ContractParameterType.INTEGER: "Integer",
    ContractParameterType.BYTE_ARRAY: "ByteArray",
    ContractParameterType.STRING: "String",
    ContractParameterType.HASH160: "Hash160",
    ContractParameterType.HASH256: "Hash256",
    ContractParameterType.PUBLIC_KEY: "PublicKey",
    ContractParameterType.SIGNATURE: "Signature",
    ContractParameterType.ARRAY: "Array",
    ContractParameterType.MAP: "Map",
    ContractParameterType.INTEROP_INTERFACE: "InteropInterface",
    ContractParameterType.VOID: "Void",
}

PARAMETER_NAME_TO_TYPE: dict[str, ContractParameterType] = {
    name: value for value, name in PARAMETER_TYPE_TO_NAME.items()
}


@dataclass
class ContractParameterDefinition:
    """Represents a parameter of a contract method or event."""

    name: str = ""
    type: ContractParameterType = ContractParameterType.ANY

    def to_json(self) -> dict[str, Any]:
        """Convert to JSON object."""
        return {
            "name": self.name,
            "type": PARAMETER_TYPE_TO_NAME[self.type]
        }

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> ContractParameterDefinition:
        """Create from JSON object."""
        type_str = json["type"] if "type" in json else "Any"
        if type_str not in PARAMETER_NAME_TO_TYPE:
            raise ValueError(f"Type({type_str}) in ContractParameterDefinition is not valid")
        param_type = PARAMETER_NAME_TO_TYPE[type_str]
        name = json.get("name", "")
        # C# FromJson: empty name and Void/undefined types are rejected.
        if not name:
            raise ValueError("Name in ContractParameterDefinition is empty")
        if param_type == ContractParameterType.VOID:
            raise ValueError(f"Type({type_str}) in ContractParameterDefinition is not valid")
        return cls(
            name=name,
            type=param_type
        )
