"""Role Management contract."""

from __future__ import annotations
from enum import IntEnum
from neo.native.native_contract import NativeContract
from neo.types import UInt160


class Role(IntEnum):
    """Node roles."""
    STATE_VALIDATOR = 4
    ORACLE = 8
    NEO_FS_ALPHABET_NODE = 16
    P2P_NOTARY = 32


class RoleManagement(NativeContract):
    """Manages node roles."""
    
    id: int = -8
    name: str = "RoleManagement"
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("49cf4e5378ffcd4dec034fd98a174c5491e395e2")[::-1])
