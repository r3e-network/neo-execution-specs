"""Neo N3 Signers."""

from dataclasses import dataclass, field
from typing import List, Optional
from neo.network.payloads.witness_scope import WitnessScope


@dataclass
class Signer:
    """Transaction signer."""
    account: Optional[object] = None
    scopes: int = WitnessScope.CALLED_BY_ENTRY
    allowed_contracts: List[bytes] = field(default_factory=list)
    allowed_groups: List[bytes] = field(default_factory=list)
    rules: List = field(default_factory=list)
    
    @property
    def size(self) -> int:
        """Get serialized size."""
        size = 20 + 1  # account + scopes
        if self.scopes & WitnessScope.CUSTOM_CONTRACTS:
            size += 1 + len(self.allowed_contracts) * 20
        if self.scopes & WitnessScope.CUSTOM_GROUPS:
            size += 1 + len(self.allowed_groups) * 33
        return size
