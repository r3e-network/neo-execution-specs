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
    
    def get_designated_by_role(self, snapshot, role: Role, index: int):
        """Get nodes designated for a role at block index."""
        from neo.crypto.ecc import ECPoint
        key = self._create_key(role, index)
        data = snapshot.storage_get(key) if snapshot else None
        if data is None:
            return []
        return self._deserialize_nodes(data)
    
    def _create_key(self, role: Role, index: int) -> bytes:
        """Create storage key for role designation."""
        prefix = bytes([11])  # Prefix_Designation
        return bytes(self.hash) + prefix + bytes([role]) + index.to_bytes(4, 'little')
    
    def _deserialize_nodes(self, data: bytes) -> list:
        """Deserialize node list from storage."""
        from neo.crypto.ecc.point import ECPoint
        from neo.crypto.ecc.curve import SECP256R1
        nodes = []
        offset = 0
        count = data[offset]
        offset += 1
        for _ in range(count):
            point_data = data[offset:offset + 33]
            nodes.append(ECPoint.decode(point_data, SECP256R1))
            offset += 33
        return nodes
