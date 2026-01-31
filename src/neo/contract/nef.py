"""NEF (Neo Executable Format) file."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import struct


@dataclass
class MethodToken:
    """Method token for contract calls."""
    hash: bytes  # UInt160
    method: str
    parameters_count: int
    has_return_value: bool
    call_flags: int


@dataclass
class NefFile:
    """Neo Executable Format container."""
    
    MAGIC: int = 0x3346454E  # "NEF3"
    
    compiler: str = ""
    source: str = ""
    tokens: List[MethodToken] = field(default_factory=list)
    script: bytes = b""
    checksum: int = 0
