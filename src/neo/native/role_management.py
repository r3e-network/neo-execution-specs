"""Role Management contract.

Reference: Neo.SmartContract.Native.RoleManagement
"""

from __future__ import annotations
from enum import IntEnum
from typing import Any

from neo.hardfork import Hardfork
from neo.native.native_contract import NativeContract, CallFlags


class Role(IntEnum):
    """Node roles."""

    STATE_VALIDATOR = 4
    ORACLE = 8
    NEO_FS_ALPHABET_NODE = 16
    P2P_NOTARY = 32


# Valid role values for validation
_VALID_ROLES = frozenset(r.value for r in Role)

# Storage prefix (matches C# RoleManagement.Prefix_Designation)
PREFIX_DESIGNATION = 11


class RoleManagement(NativeContract):
    """Manages node roles.

    Allows the committee to designate public keys for specific network
    roles (validators, oracles, NeoFS alphabet nodes, P2P notary).
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self) -> str:
        return "RoleManagement"

    def _register_methods(self) -> None:
        """Register RoleManagement contract methods."""
        super()._register_methods()
        self._register_method(
            "getDesignatedByRole",
            self.get_designated_by_role,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
        )
        self._register_method(
            "designateAsRole",
            self.designate_as_role,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
        )

    def _register_events(self) -> None:
        """Register RoleManagement events."""
        super()._register_events()
        self._register_event(
            "Designation",
            [("Role", "Integer"), ("BlockIndex", "Integer")],
            order=0,
            deprecated_in=Hardfork.HF_ECHIDNA,
        )
        self._register_event(
            "Designation",
            [
                ("Role", "Integer"),
                ("BlockIndex", "Integer"),
                ("Old", "Array"),
                ("New", "Array"),
            ],
            order=0,
            active_in=Hardfork.HF_ECHIDNA,
        )

    def get_designated_by_role(self, snapshot: Any, role: Role, index: int) -> list:
        """Get nodes designated for a role at block index.

        Seeks backwards from *index* to find the most recent designation
        at or before the requested block height.

        Args:
            snapshot: Storage snapshot
            role: The node role to query
            index: Block index

        Returns:
            List of ECPoint public keys designated for the role
        """
        if not isinstance(role, int) or role not in _VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        if index < 0:
            raise ValueError("Index must be non-negative")

        if snapshot is None:
            return []

        prefix = self._create_storage_key(PREFIX_DESIGNATION, bytes([role]))
        prefix_bytes: bytes
        if hasattr(prefix, "key") and isinstance(prefix.key, bytes):
            prefix_bytes = prefix.key
        else:
            prefix_bytes = bytes(prefix) if hasattr(prefix, "__bytes__") else b""

        best_value = None
        best_index = -1
        for full_key, value in snapshot.find(prefix):
            full_key_bytes: bytes
            if hasattr(full_key, "key") and isinstance(full_key.key, bytes):
                full_key_bytes = full_key.key
            elif hasattr(full_key, "__bytes__"):
                full_key_bytes = bytes(full_key)
            else:
                full_key_bytes = b""
            suffix = full_key_bytes[len(prefix_bytes) :]
            if len(suffix) >= 4:
                stored_index = int.from_bytes(suffix[:4], "little")
                if stored_index <= index and stored_index > best_index:
                    best_index = stored_index
                    best_value = value

        if best_value is None:
            return []
        return self._deserialize_nodes(best_value)

    def designate_as_role(
        self,
        engine: Any,
        role: Role,
        nodes: list,
    ) -> None:
        """Designate public keys for a network role. Committee only.

        Args:
            engine: Application engine
            role: The role to designate nodes for
            nodes: List of ECPoint public keys

        Raises:
            ValueError: If role is invalid or nodes list is empty
            PermissionError: If caller is not the committee
        """
        if not isinstance(role, int) or role not in _VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        if not nodes:
            raise ValueError("Nodes list must not be empty")
        if hasattr(engine, "check_committee") and not engine.check_committee():
            raise PermissionError("Committee signature required")

        snapshot = engine.snapshot if hasattr(engine, "snapshot") else None
        if snapshot is None:
            raise RuntimeError("Snapshot not available")

        block_index = 0
        if hasattr(snapshot, "persisting_block") and snapshot.persisting_block:
            block_index = getattr(snapshot.persisting_block, "index", 0)

        # Sort nodes by encoded form for deterministic storage
        sorted_nodes = sorted(nodes, key=lambda n: n.encode(compressed=True))

        key = self._create_storage_key(
            PREFIX_DESIGNATION, bytes([role]) + (block_index + 1).to_bytes(4, "little")
        )
        data = self._serialize_nodes(sorted_nodes)
        snapshot.put(key, data)

    def _serialize_nodes(self, nodes: list) -> bytes:
        """Serialize node list to storage format."""
        result = bytearray()
        result.append(len(nodes))
        for node in nodes:
            result.extend(node.encode(compressed=True))
        return bytes(result)

    def _deserialize_nodes(self, data: bytes) -> list:
        """Deserialize node list from storage."""
        from neo.crypto.ecc.point import ECPoint
        from neo.crypto.ecc.curve import SECP256R1

        nodes = []
        offset = 0
        count = data[offset]
        offset += 1
        for _ in range(count):
            point_data = data[offset : offset + 33]
            nodes.append(ECPoint.decode(point_data, SECP256R1))
            offset += 33
        return nodes
