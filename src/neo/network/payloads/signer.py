"""Neo N3 Signers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from neo.network.payloads.witness_scope import WitnessScope

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter
    from neo.types.uint160 import UInt160


@dataclass
class Signer:
    """Transaction signer."""

    account: "UInt160 | None" = None
    scopes: WitnessScope = WitnessScope.CALLED_BY_ENTRY
    allowed_contracts: list[bytes] = field(default_factory=list)
    allowed_groups: list[bytes] = field(default_factory=list)
    rules: list[Any] = field(default_factory=list)

    @property
    def size(self) -> int:
        """Get serialized size."""
        size = 20 + 1  # account + scopes
        if self.scopes & WitnessScope.CUSTOM_CONTRACTS:
            size += 1 + len(self.allowed_contracts) * 20
        if self.scopes & WitnessScope.CUSTOM_GROUPS:
            size += 1 + len(self.allowed_groups) * 33
        if self.scopes & WitnessScope.WITNESS_RULES:
            size += 1 + sum(r.size for r in self.rules)
        return size

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the signer."""
        if self.account is not None:
            writer.write_bytes(self.account.data)
        else:
            writer.write_bytes(b"\x00" * 20)

        writer.write_byte(int(self.scopes))

        if self.scopes & WitnessScope.CUSTOM_CONTRACTS:
            writer.write_var_int(len(self.allowed_contracts))
            for contract in self.allowed_contracts:
                writer.write_bytes(contract)

        if self.scopes & WitnessScope.CUSTOM_GROUPS:
            writer.write_var_int(len(self.allowed_groups))
            for group in self.allowed_groups:
                writer.write_bytes(group)

        if self.scopes & WitnessScope.WITNESS_RULES:
            writer.write_var_int(len(self.rules))
            for rule in self.rules:
                rule.serialize(writer)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Signer":
        """Deserialize a signer."""
        from neo.types.uint160 import UInt160

        account = UInt160(reader.read_bytes(20))
        scopes = WitnessScope(reader.read_byte())

        allowed_contracts: list[bytes] = []
        if scopes & WitnessScope.CUSTOM_CONTRACTS:
            count = reader.read_var_int(16)
            allowed_contracts = [reader.read_bytes(20) for _ in range(count)]

        allowed_groups: list[bytes] = []
        if scopes & WitnessScope.CUSTOM_GROUPS:
            count = reader.read_var_int(16)
            allowed_groups = [reader.read_bytes(33) for _ in range(count)]

        rules: list[Any] = []
        if scopes & WitnessScope.WITNESS_RULES:
            from neo.network.payloads.witness_rule import WitnessRule

            count = reader.read_var_int(16)
            rules = [WitnessRule.deserialize(reader) for _ in range(count)]

        return cls(
            account=account,
            scopes=scopes,
            allowed_contracts=allowed_contracts,
            allowed_groups=allowed_groups,
            rules=rules,
        )
