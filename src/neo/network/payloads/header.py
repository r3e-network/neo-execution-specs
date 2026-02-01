"""
Header - Represents a Neo N3 block header.

Reference: Neo.Network.P2P.Payloads.Header
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from neo.types.uint256 import UInt256
from neo.types.uint160 import UInt160

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter
    from neo.network.payloads.witness import Witness


@dataclass
class Header:
    """Represents a Neo N3 block header."""
    
    version: int = 0
    prev_hash: UInt256 = field(default_factory=lambda: UInt256.ZERO)
    merkle_root: UInt256 = field(default_factory=lambda: UInt256.ZERO)
    timestamp: int = 0
    nonce: int = 0
    index: int = 0
    primary_index: int = 0
    next_consensus: UInt160 = field(default_factory=lambda: UInt160.ZERO)
    witness: "Witness" = None
    _hash: UInt256 = field(default=None, repr=False)
