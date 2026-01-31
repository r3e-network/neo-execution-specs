"""Contract Manifest."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ContractAbi:
    """Contract ABI definition."""
    methods: List[ContractMethod] = field(default_factory=list)
    events: List[ContractEvent] = field(default_factory=list)


@dataclass
class ContractMethod:
    """Contract method definition."""
    name: str
    parameters: List[ContractParameter] = field(default_factory=list)
    return_type: str = "Void"
    offset: int = 0
    safe: bool = False


@dataclass
class ContractParameter:
    """Contract parameter."""
    name: str
    type: str


@dataclass
class ContractEvent:
    """Contract event."""
    name: str
    parameters: List[ContractParameter] = field(default_factory=list)
