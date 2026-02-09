"""Neo N3 Contract Manifest implementation."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import IntFlag


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
    name: str = ""
    groups: List[ContractGroup] = field(default_factory=list)
    supported_standards: List[str] = field(default_factory=list)
    abi: Optional[Any] = None
    permissions: List[ContractPermission] = field(default_factory=list)
    trusts: List[ContractPermissionDescriptor] = field(default_factory=list)
    extra: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON."""
        return {
            "name": self.name,
            "groups": [],
            "supportedstandards": self.supported_standards,
            "abi": None,
            "permissions": [],
            "trusts": [],
            "extra": self.extra,
        }
