"""
Signer - Represents a transaction signer.

Reference: Neo.Network.P2P.Payloads.Signer
"""

from dataclasses import dataclass, field
from typing import List, Optional
from neo.network.payloads.witness_scope import WitnessScope
from neo.types.uint160 import UInt160


@dataclass
class Signer:
    """
    Represents a signer of a transaction.
    """
    
    account: UInt160
    """The account script hash of the signer."""
    
    scopes: WitnessScope = WitnessScope.CALLED_BY_ENTRY
    """The scope of the witness."""
    
    allowed_contracts: List[UInt160] = field(default_factory=list)
    """Contracts allowed when scope includes CUSTOM_CONTRACTS."""
    
    allowed_groups: List[bytes] = field(default_factory=list)
    """Groups allowed when scope includes CUSTOM_GROUPS."""
    
    rules: List["WitnessRule"] = field(default_factory=list)
    """Witness rules when scope includes WITNESS_RULES."""
