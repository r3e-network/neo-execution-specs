"""
Transaction - Represents a Neo N3 transaction.

Reference: Neo.Network.P2P.Payloads.Transaction
"""

from dataclasses import dataclass, field
from typing import List, Optional
from neo.types.uint256 import UInt256
from neo.crypto.hash import hash256
from neo.network.payloads.signer import Signer
from neo.network.payloads.witness import Witness
from neo.network.payloads.transaction_attribute import TransactionAttribute


# Constants
MAX_TRANSACTION_SIZE = 102400
MAX_TRANSACTION_ATTRIBUTES = 16
HEADER_SIZE = 1 + 4 + 8 + 8 + 4  # Version + Nonce + SystemFee + NetworkFee + ValidUntilBlock


@dataclass
class Transaction:
    """
    Represents a Neo N3 transaction.
    """
    
    version: int = 0
    """Transaction version."""
    
    nonce: int = 0
    """Random number to avoid hash collision."""
    
    system_fee: int = 0
    """Fee paid for script execution."""
    
    network_fee: int = 0
    """Fee paid for transaction size."""
    
    valid_until_block: int = 0
    """Block height until which the transaction is valid."""
    
    signers: List[Signer] = field(default_factory=list)
    """Transaction signers."""
    
    attributes: List[TransactionAttribute] = field(default_factory=list)
    """Transaction attributes."""
    
    script: bytes = b""
    """Contract invocation script."""
    
    witnesses: List[Witness] = field(default_factory=list)
    """Transaction witnesses."""
    
    _hash: Optional[UInt256] = field(default=None, repr=False)
    
    @property
    def hash(self) -> UInt256:
        """Get the transaction hash."""
        if self._hash is None:
            self._hash = UInt256(hash256(self._get_hash_data()))
        return self._hash
    
    @property
    def sender(self) -> bytes:
        """Get the sender (first signer's account)."""
        if self.signers:
            return self.signers[0].account.to_bytes()
        return b"\x00" * 20
    
    def _get_hash_data(self) -> bytes:
        """Get data for hash calculation."""
        # Simplified - actual implementation needs proper serialization
        data = bytearray()
        data.append(self.version)
        data.extend(self.nonce.to_bytes(4, 'little'))
        data.extend(self.system_fee.to_bytes(8, 'little', signed=True))
        data.extend(self.network_fee.to_bytes(8, 'little', signed=True))
        data.extend(self.valid_until_block.to_bytes(4, 'little'))
        # Add signers, attributes, script...
        data.extend(self.script)
        return bytes(data)
