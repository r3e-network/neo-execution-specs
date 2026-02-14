"""Neo N3 Contract Manifest implementation."""

from dataclasses import dataclass, field
from enum import IntFlag
from typing import Any, Dict, List, Optional


class ContractPermissionDescriptor:
    """Permission descriptor for contract calls."""
    
    def __init__(self, value: Any = None):
        self.hash: Optional[bytes] = None
        self.group: Optional[bytes] = None
        self.is_wildcard = value == "*"
        
        if isinstance(value, bytes) and len(value) == 20:
            self.hash = value
        elif isinstance(value, bytes) and len(value) == 33:
            self.group = value


@dataclass
class ContractPermission:
    """Contract permission."""

    contract: ContractPermissionDescriptor
    methods: List[str] = field(default_factory=list)
    is_wildcard_methods: bool = False


@dataclass  
class ContractGroup:
    """Contract group for trust."""

    pubkey: bytes  # 33 bytes compressed
    signature: bytes  # 64 bytes


class ContractFeatures(IntFlag):
    """Contract features."""

    NO_PROPERTY = 0
    HAS_STORAGE = 1
    PAYABLE = 2


@dataclass
class ContractManifest:
    """Contract manifest."""

    MAX_LENGTH = 0xFFFF

    name: str = ""
    groups: List[ContractGroup] = field(default_factory=list)
    supported_standards: List[str] = field(default_factory=list)
    abi: Optional[Any] = None
    permissions: List[ContractPermission] = field(default_factory=list)
    trusts: List[ContractPermissionDescriptor] = field(default_factory=list)
    extra: Optional[Dict[str, Any]] = None

    @staticmethod
    def _serialize_item(item: Any) -> Any:
        """Serialize a single item to a JSON-compatible value."""
        import dataclasses

        if hasattr(item, 'to_json'):
            return item.to_json()
        elif dataclasses.is_dataclass(item) and not isinstance(item, type):
            return dataclasses.asdict(item)
        elif isinstance(item, (str, int, float, bool, type(None))):
            return item
        else:
            return str(item)

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON."""
        import json

        result = {
            "name": self.name,
            "groups": [self._serialize_item(g) for g in self.groups] if self.groups else [],
            "supportedstandards": self.supported_standards,
            "abi": self._serialize_item(self.abi) if self.abi is not None else None,
            "permissions": [self._serialize_item(p) for p in self.permissions] if self.permissions else [],
            "trusts": [self._serialize_item(t) for t in self.trusts] if self.trusts else [],
            "extra": self.extra,
        }
        # Validate serialized size
        serialized = json.dumps(result, separators=(',', ':'))
        if len(serialized.encode('utf-8')) > self.MAX_LENGTH:
            raise ValueError(
                f"Manifest JSON exceeds maximum length of {self.MAX_LENGTH}"
            )
        return result
