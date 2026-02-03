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
        # Signers, attributes, script...
        data.extend(self.script)
        return bytes(data)
    
    def serialize(self) -> bytes:
        """Serialize transaction."""
        return self._serialize_unsigned()
