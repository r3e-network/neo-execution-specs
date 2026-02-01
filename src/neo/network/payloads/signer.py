"""
Signer - Represents a transaction signer.

Reference: Neo.Network.P2P.Payloads.Signer
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from neo.network.payloads.witness_scope import WitnessScope
from neo.types.uint160 import UInt160

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter

# Maximum subitems for contracts/groups/rules
MAX_SUBITEMS = 16


@dataclass
class Signer:
    """Represents a signer of a transaction."""
    
    account: UInt160 = field(default_factory=lambda: UInt160.ZERO)
    """The account script hash of the signer."""
    
    scopes: WitnessScope = WitnessScope.CALLED_BY_ENTRY
    """The scope of the witness."""
    
    allowed_contracts: List[UInt160] = field(default_factory=list)
    """Contracts allowed when scope includes CUSTOM_CONTRACTS."""
    
    allowed_groups: List[bytes] = field(default_factory=list)
    """Groups (EC points) allowed when scope includes CUSTOM_GROUPS."""
    
    rules: List["WitnessRule"] = field(default_factory=list)
    """Witness rules when scope includes WITNESS_RULES."""
    
    @property
    def size(self) -> int:
        """Get the serialized size."""
        from neo.network.payloads.witness import _get_var_size
        size = UInt160.LENGTH + 1  # Account + Scopes
        if self.scopes & WitnessScope.CUSTOM_CONTRACTS:
            size += _get_var_size(len(self.allowed_contracts))
            size += len(self.allowed_contracts) * UInt160.LENGTH
        if self.scopes & WitnessScope.CUSTOM_GROUPS:
            size += _get_var_size(len(self.allowed_groups))
            size += sum(len(g) for g in self.allowed_groups)
        if self.scopes & WitnessScope.WITNESS_RULES:
            size += _get_var_size(len(self.rules))
            size += sum(r.size for r in self.rules)
        return size
    
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the signer."""
        writer.write_uint160(self.account)
        writer.write_byte(int(self.scopes))
        if self.scopes & WitnessScope.CUSTOM_CONTRACTS:
            writer.write_var_int(len(self.allowed_contracts))
            for contract in self.allowed_contracts:
                writer.write_uint160(contract)
        if self.scopes & WitnessScope.CUSTOM_GROUPS:
            writer.write_var_int(len(self.allowed_groups))
            for group in self.allowed_groups:
                writer.write_ec_point(group)
        if self.scopes & WitnessScope.WITNESS_RULES:
            writer.write_var_int(len(self.rules))
            for rule in self.rules:
                rule.serialize(writer)
    
    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Signer":
        """Deserialize a signer."""
        account = reader.read_uint160()
        scopes = WitnessScope(reader.read_byte())
        
        # Validate scopes
        valid_flags = (
            WitnessScope.CALLED_BY_ENTRY |
            WitnessScope.CUSTOM_CONTRACTS |
            WitnessScope.CUSTOM_GROUPS |
            WitnessScope.WITNESS_RULES |
            WitnessScope.GLOBAL
        )
        if scopes & ~valid_flags:
            raise ValueError(f"Invalid scopes: {scopes}")
        if scopes & WitnessScope.GLOBAL and scopes != WitnessScope.GLOBAL:
            raise ValueError("Global scope cannot be combined with other flags")
        
        allowed_contracts = []
        if scopes & WitnessScope.CUSTOM_CONTRACTS:
            count = reader.read_var_int(MAX_SUBITEMS)
            for _ in range(count):
                allowed_contracts.append(reader.read_uint160())
        
        allowed_groups = []
        if scopes & WitnessScope.CUSTOM_GROUPS:
            count = reader.read_var_int(MAX_SUBITEMS)
            for _ in range(count):
                allowed_groups.append(reader.read_ec_point())
        
        rules = []
        if scopes & WitnessScope.WITNESS_RULES:
            from neo.network.payloads.witness_rule import WitnessRule
            count = reader.read_var_int(MAX_SUBITEMS)
            for _ in range(count):
                rules.append(WitnessRule.deserialize(reader))
        
        return cls(
            account=account,
            scopes=scopes,
            allowed_contracts=allowed_contracts,
            allowed_groups=allowed_groups,
            rules=rules
        )
