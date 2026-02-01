"""
Protocol Settings for Neo N3.

Reference: Neo.ProtocolSettings
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ProtocolSettings:
    """Neo N3 protocol configuration."""
    
    network: int = 860833102  # MainNet magic
    address_version: int = 53
    validators_count: int = 7
    committee_members_count: int = 21
    milliseconds_per_block: int = 15000
    max_transactions_per_block: int = 512
    memory_pool_max_transactions: int = 50000
    max_traceable_blocks: int = 2102400
    initial_gas_distribution: int = 52_000_000 * 100_000_000
    
    # Hardforks
    hardforks: Dict[str, int] = field(default_factory=dict)
    
    # Standby committee (simplified)
    standby_committee: List[bytes] = field(default_factory=list)
