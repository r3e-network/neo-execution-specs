"""Role Management contract.

Reference: Neo.SmartContract.Native.RoleManagement
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from neo.exceptions import InvalidOperationException
from neo.hardfork import Hardfork
from neo.native.native_contract import CallFlags, NativeContract


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
        # C# uses uint for index; the spec uses signed int so keep the lower
        # bound. (RoleManagement.cs:54-56 enforces only the upper bound.)
        if index < 0:
            raise ValueError("Index must be non-negative")

        if snapshot is None:
            return []

        # C# v3.10.0 RoleManagement.cs:54-56: fault when the requested index
        # is more than one block ahead of the chain tip.
        current_index = self._ledger_current_index(snapshot)
        if current_index + 1 < index:
            raise InvalidOperationException(
                f"Index {index} exceeds current index + 1 ({current_index + 1})"
            )

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
                # Storage key index is 4-byte big-endian (KeyBuilder.AddBigEndian).
                stored_index = int.from_bytes(suffix[:4], "big")
                if stored_index <= index and stored_index > best_index:
                    best_index = stored_index
                    best_value = value

        if best_value is None:
            return []
        return self._deserialize_nodes(best_value)

    def _ledger_current_index(self, snapshot: Any) -> int:
        """Return Ledger.CurrentIndex for *snapshot*.

        Mirrors C# Ledger.CurrentIndex(snapshot). When the Ledger native is
        not registered or its current-block record is absent, this returns 0
        (the same default the Ledger native uses when uninitialized).
        """
        ledger = NativeContract.get_contract_by_name("LedgerContract")
        if ledger is None or not hasattr(ledger, "current_index"):
            return 0
        try:
            return ledger.current_index(snapshot)
        except Exception:
            return 0

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
        # C# RoleManagement.cs:65-72 ordering: nodes-bounds, role, committee.
        if len(nodes) == 0 or len(nodes) > 32:
            raise InvalidOperationException(
                f"Nodes count {len(nodes)} must be between 1 and 32"
            )
        if not isinstance(role, int) or role not in _VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        if hasattr(engine, "check_committee") and not engine.check_committee():
            raise PermissionError("Committee signature required")

        snapshot = engine.snapshot if hasattr(engine, "snapshot") else None
        if snapshot is None:
            raise RuntimeError("Snapshot not available")

        # C# RoleManagement.cs:73-74: fault when there is no persisting block.
        persisting_block = getattr(engine, "persisting_block", None)
        if persisting_block is None and snapshot is not None:
            persisting_block = getattr(snapshot, "persisting_block", None)
        if persisting_block is None:
            raise InvalidOperationException("Persisting block is null")
        block_index = getattr(persisting_block, "index", 0)

        # C# RoleManagement.cs:76-79: storage index = PersistingBlock.Index + 1,
        # fault if already designated at this index.
        index = block_index + 1
        key = self._create_storage_key(
            PREFIX_DESIGNATION, bytes([role]) + index.to_bytes(4, "big")
        )
        if hasattr(snapshot, "contains") and snapshot.contains(key):
            raise InvalidOperationException("Role already designated")

        # C# RoleManagement.cs:81-82: reject duplicate public keys.
        encoded = [n.encode(compressed=True) for n in nodes]
        if len(set(encoded)) != len(encoded):
            raise InvalidOperationException("Duplicate publickeys are not allowed")

        # Sort nodes by encoded form for deterministic storage
        sorted_nodes = sorted(nodes, key=lambda n: n.encode(compressed=True))
        data = self._serialize_nodes(sorted_nodes)
        snapshot.put(key, data)

        # C# RoleManagement.cs:88-98: emit the Designation notification.
        self._emit_designation(engine, snapshot, role, block_index, index, nodes)

    def _emit_designation(
        self,
        engine: Any,
        snapshot: Any,
        role: int,
        block_index: int,
        index: int,
        nodes: list,
    ) -> None:
        """Emit the Designation notification, matching C# RoleManagement.cs:88-98."""
        if not hasattr(engine, "send_notification"):
            return
        try:
            from neo.vm.types import Array, ByteString, Integer
        except Exception:
            return

        echidna = False
        try:
            echidna = self.is_hardfork_enabled(engine, Hardfork.HF_ECHIDNA)
        except Exception:
            echidna = False

        if echidna:
            old_points = self.get_designated_by_role(snapshot, role, index - 1)
            old_nodes = Array(
                items=[ByteString(p.encode(compressed=True)) for p in old_points]
            )
            new_nodes = Array(
                items=[ByteString(n.encode(compressed=True)) for n in nodes]
            )
            state = Array(
                items=[Integer(int(role)), Integer(block_index), old_nodes, new_nodes]
            )
        else:
            state = Array(items=[Integer(int(role)), Integer(block_index)])
        engine.send_notification(self.hash, "Designation", state)

    def _serialize_nodes(self, nodes: list) -> bytes:
        """Serialize node list to storage format."""
        result = bytearray()
        result.append(len(nodes))
        for node in nodes:
            result.extend(node.encode(compressed=True))
        return bytes(result)

    def _deserialize_nodes(self, data: bytes) -> list:
        """Deserialize node list from storage."""
        from neo.crypto.ecc.curve import SECP256R1
        from neo.crypto.ecc.point import ECPoint

        nodes = []
        offset = 0
        count = data[offset]
        offset += 1
        for _ in range(count):
            point_data = data[offset : offset + 33]
            nodes.append(ECPoint.decode(point_data, SECP256R1))
            offset += 33
        return nodes
