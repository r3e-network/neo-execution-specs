"""Neo N3 Account implementation."""

from __future__ import annotations
from dataclasses import dataclass, field

from enum import IntEnum

from neo.crypto.hash import hash160
from neo.wallets.key_pair import KeyPair

class AccountType(IntEnum):
    """Account type enumeration."""
    STANDARD = 0
    MULTI_SIG = 1
    CONTRACT = 2

@dataclass
class Account:
    """Represents a Neo account."""
    
    script_hash: bytes
    label: str = ""
    is_default: bool = False
    lock: bool = False
    key_pair: KeyPair | None = None
    contract: "Contract" | None = None
    extra: dict = field(default_factory=dict)
    
    @classmethod
    def from_key_pair(cls, key_pair: KeyPair, label: str = "") -> "Account":
        """Create account from key pair."""
        # Create verification script
        script = create_signature_script(key_pair.public_key)
        script_hash = hash160(script)
        
        contract = Contract(
            script=script,
            parameters=[ContractParameter("signature", "Signature")]
        )
        
        return cls(
            script_hash=script_hash,
            label=label,
            key_pair=key_pair,
            contract=contract
        )
    
    @classmethod
    def from_script_hash(cls, script_hash: bytes, label: str = "") -> "Account":
        """Create watch-only account from script hash."""
        return cls(script_hash=script_hash, label=label)
    
    @property
    def address(self) -> str:
        """Get Neo address."""
        return script_hash_to_address(self.script_hash)
    
    @property
    def has_key(self) -> bool:
        """Check if account has private key."""
        return self.key_pair is not None
    
    def sign(self, message: bytes) -> bytes:
        """Sign message with account key."""
        if not self.key_pair:
            raise ValueError("Account has no private key")
        return self.key_pair.sign(message)

@dataclass
class ContractParameter:
    """Contract parameter definition."""
    name: str
    type: str

@dataclass
class Contract:
    """Account contract."""
    script: bytes
    parameters: list[ContractParameter] = field(default_factory=list)
    deployed: bool = False

def create_signature_script(public_key) -> bytes:
    """Create signature verification script."""
    from neo.vm.opcode import OpCode
    
    # PUSHDATA1 <pubkey> SYSCALL System.Crypto.CheckSig
    pubkey_bytes = public_key.encode(compressed=True)
    
    script = bytearray()
    script.append(OpCode.PUSHDATA1)
    script.append(len(pubkey_bytes))
    script.extend(pubkey_bytes)
    script.append(OpCode.SYSCALL)
    # System.Crypto.CheckSig hash
    script.extend(bytes.fromhex("0a906ad4"))
    
    return bytes(script)

def script_hash_to_address(script_hash: bytes) -> str:
    """Convert script hash to Neo address."""
    from neo.wallets.key_pair import base58_check_encode
    
    # Neo N3 address version
    ADDRESS_VERSION = 0x35
    data = bytes([ADDRESS_VERSION]) + script_hash
    return base58_check_encode(data)

def address_to_script_hash(address: str) -> bytes:
    """Convert Neo address to script hash."""
    from neo.wallets.key_pair import base58_check_decode
    
    data = base58_check_decode(address)
    if data[0] != 0x35:
        raise ValueError("Invalid address version")
    return data[1:21]
