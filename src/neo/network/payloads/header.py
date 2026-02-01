"""
Header - Represents a Neo N3 block header.

Reference: Neo.Network.P2P.Payloads.Header
"""

from dataclasses import dataclass, field
from typing import Optional
from neo.types.uint256 import UInt256
from neo.types.uint160 import UInt160
from neo.crypto.hash import hash256


@dataclass
class Header:
    """Represents a Neo N3 block header."""
    
    version: int = 0
    """Block version."""
    
    prev_hash: UInt256 = field(default_factory=lambda: UInt256(b"\x00" * 32))
    """Hash of the previous block."""
    
    merkle_root: UInt256 = field(default_factory=lambda: UInt256(b"\x00" * 32))
    """Merkle root of transactions."""
    
    timestamp: int = 0
    """Block timestamp in milliseconds."""
    
    nonce: int = 0
    """Block nonce."""
    
    index: int = 0
    """Block height/index."""
    
    primary_index: int = 0
    """Index of the primary consensus node."""
    
    next_consensus: UInt160 = field(default_factory=lambda: UInt160(b"\x00" * 20))
    """Script hash of next consensus."""
    
    witness: Optional["Witness"] = None
    """Block witness."""
    
    _hash: Optional[UInt256] = field(default=None, repr=False)
