"""Neo N3 Signers."""

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from neo.network.payloads.witness_scope import WitnessScope

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class Signer:
    """Transaction signer."""
    account: Optional[object] = None
    scopes: int = WitnessScope.CALLED_BY_ENTRY
    allowed_contracts: List[bytes] = field(default_factory=list)
    allowed_groups: List[bytes] = field(default_factory=list)
    rules: List = field(default_factory=list)
    
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
        # Write account (20 bytes)
        if self.account is not None:
            writer.write_bytes(bytes(self.account))
        else:
            writer.write_bytes(b"\x00" * 20)
        
        # Write scopes
        writer.write_byte(self.scopes)
        
        # Write allowed contracts if scope includes CUSTOM_CONTRACTS
        if self.scopes & WitnessScope.CUSTOM_CONTRACTS:
            writer.write_var_int(len(self.allowed_contracts))
            for contract in self.allowed_contracts:
                writer.write_bytes(contract)
        
        # Write allowed groups if scope includes CUSTOM_GROUPS
        if self.scopes & WitnessScope.CUSTOM_GROUPS:
            writer.write_var_int(len(self.allowed_groups))
            for group in self.allowed_groups:
                writer.write_bytes(group)

        # Write rules if scope includes WITNESS_RULES
        if self.scopes & WitnessScope.WITNESS_RULES:
            writer.write_var_int(len(self.rules))
            for rule in self.rules:
                rule.serialize(writer)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Signer":
        """Deserialize a signer."""
        from neo.types.uint160 import UInt160
        
        account = UInt160(reader.read_bytes(20))
        scopes = reader.read_byte()
        
        allowed_contracts = []
        if scopes & WitnessScope.CUSTOM_CONTRACTS:
            count = reader.read_var_int(16)
            allowed_contracts = [reader.read_bytes(20) for _ in range(count)]
        
        allowed_groups = []
        if scopes & WitnessScope.CUSTOM_GROUPS:
            count = reader.read_var_int(16)
            allowed_groups = [reader.read_bytes(33) for _ in range(count)]

        rules = []
        if scopes & WitnessScope.WITNESS_RULES:
            from neo.network.payloads.witness_rule import WitnessRule
            count = reader.read_var_int(16)
            rules = [WitnessRule.deserialize(reader) for _ in range(count)]

        return cls(
            account=account,
            scopes=scopes,
            allowed_contracts=allowed_contracts,
            allowed_groups=allowed_groups,
            rules=rules
        )
