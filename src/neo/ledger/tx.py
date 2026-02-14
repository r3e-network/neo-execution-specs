"""Neo N3 Transaction class."""

from dataclasses import dataclass, field
from typing import List, Optional
import struct

from neo.ledger.transaction import Signer, Witness, TransactionAttribute
from neo.crypto.hash import hash256


@dataclass
class Transaction:
    """Neo N3 Transaction."""
    
    version: int = 0
    nonce: int = 0
    system_fee: int = 0
    network_fee: int = 0
    valid_until_block: int = 0
    signers: List[Signer] = field(default_factory=list)
    attributes: List[TransactionAttribute] = field(default_factory=list)
    script: bytes = b""
    witnesses: List[Witness] = field(default_factory=list)
    
    _hash: Optional[bytes] = field(default=None, repr=False)
    
    @property
    def hash(self) -> bytes:
        """Get transaction hash."""
        if self._hash is None:
            self._hash = hash256(self._get_hash_data())
        return self._hash
    
    @property
    def sender(self) -> bytes:
        """Get sender (first signer)."""
        return self.signers[0].account if self.signers else bytes(20)
    
    @property
    def size(self) -> int:
        """Get serialized size."""
        return len(self.serialize())
    
    def _get_hash_data(self) -> bytes:
        """Get data for hashing."""
        return self._serialize_unsigned()
    
    def _serialize_unsigned(self) -> bytes:
        """Serialize without witnesses."""
        data = bytearray()
        data.append(self.version)
        data.extend(struct.pack('<I', self.nonce))
        data.extend(struct.pack('<Q', self.system_fee))
        data.extend(struct.pack('<Q', self.network_fee))
        data.extend(struct.pack('<I', self.valid_until_block))
        # Signers
        self._write_var_int(data, len(self.signers))
        for signer in self.signers:
            data.extend(self._serialize_signer(signer))
        # Attributes
        self._write_var_int(data, len(self.attributes))
        for attr in self.attributes:
            data.extend(self._serialize_attribute(attr))
        # Script
        self._write_var_int(data, len(self.script))
        data.extend(self.script)
        return bytes(data)

    @staticmethod
    def _write_var_int(data: bytearray, value: int) -> None:
        """Write a variable-length integer into *data*."""
        if value < 0xFD:
            data.append(value)
        elif value <= 0xFFFF:
            data.append(0xFD)
            data.extend(struct.pack('<H', value))
        elif value <= 0xFFFFFFFF:
            data.append(0xFE)
            data.extend(struct.pack('<I', value))
        else:
            data.append(0xFF)
            data.extend(struct.pack('<Q', value))

    @staticmethod
    def _serialize_signer(signer: "Signer") -> bytes:
        """Serialize a single signer."""
        buf = bytearray()
        buf.extend(signer.account)          # 20 bytes UInt160
        buf.append(signer.scopes)           # 1 byte WitnessScope
        # Allowed contracts (only when CustomContracts scope bit is set)
        if signer.scopes & 0x10:
            Transaction._write_var_int(buf, len(signer.allowed_contracts))
            for h in signer.allowed_contracts:
                buf.extend(h)
        # Allowed groups (only when CustomGroups scope bit is set)
        if signer.scopes & 0x20:
            Transaction._write_var_int(buf, len(signer.allowed_groups))
            for g in signer.allowed_groups:
                buf.extend(g)
        # Rules (only when WitnessRules scope bit is set)
        if signer.scopes & 0x40:
            Transaction._write_var_int(buf, len(signer.rules))
            for r in signer.rules:
                buf.extend(r if isinstance(r, bytes) else bytes(r))
        return bytes(buf)

    @staticmethod
    def _serialize_attribute(attr: "TransactionAttribute") -> bytes:
        """Serialize a single transaction attribute."""
        buf = bytearray()
        buf.append(attr.type)
        buf.extend(attr.data)
        return bytes(buf)
    
    def serialize(self) -> bytes:
        """Serialize transaction."""
        return self._serialize_unsigned()
