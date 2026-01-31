"""Contract Manifest."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from neo.contract.abi import ContractAbi


@dataclass
class ContractPermission:
    """Permission to call other contracts."""
    contract: str  # "*" or contract hash
    methods: List[str]  # ["*"] or method names


@dataclass
class ContractManifest:
    """Contract metadata and permissions."""
    
    name: str = ""
    groups: List[Dict[str, Any]] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    supported_standards: List[str] = field(default_factory=list)
    abi: ContractAbi = field(default_factory=ContractAbi)
    permissions: List[ContractPermission] = field(default_factory=list)
    trusts: List[str] = field(default_factory=list)
    extra: Optional[Dict[str, Any]] = None
