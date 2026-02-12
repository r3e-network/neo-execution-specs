"""Type definitions for Neo t8n tool.

Defines input/output data structures for state transition.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import IntEnum


class VMStateResult(IntEnum):
    """VM execution state."""
    HALT = 1
    FAULT = 2


@dataclass
class StorageEntry:
    """Storage key-value entry."""
    key: str  # hex-encoded
    value: str  # hex-encoded


@dataclass
class AccountState:
    """Account state in allocation.
    
    Represents the state of a single account including:
    - NEO balance
    - GAS balance  
    - Contract storage (if contract account)
    - NEF script (if contract account)
    """
    neo_balance: int = 0
    gas_balance: int = 0
    storage: Dict[str, str] = field(default_factory=dict)  # hex key -> hex value
    nef: Optional[str] = None  # hex-encoded NEF
    manifest: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccountState":
        """Create AccountState from dictionary."""
        return cls(
            neo_balance=int(data.get("neoBalance", data.get("neo_balance", 0))),
            gas_balance=int(data.get("gasBalance", data.get("gas_balance", 0))),
            storage=data.get("storage", {}),
            nef=data.get("nef"),
            manifest=data.get("manifest"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {}
        if self.neo_balance > 0:
            result["neoBalance"] = self.neo_balance
        if self.gas_balance > 0:
            result["gasBalance"] = self.gas_balance
        if self.storage:
            result["storage"] = self.storage
        if self.nef:
            result["nef"] = self.nef
        if self.manifest:
            result["manifest"] = self.manifest
        return result


# Type alias for allocation mapping
Alloc = Dict[str, AccountState]  # address (hex) -> AccountState


@dataclass
class SignerInput:
    """Transaction signer input."""
    account: str  # hex-encoded UInt160
    scopes: int = 1  # WitnessScope.CALLED_BY_ENTRY
    allowed_contracts: List[str] = field(default_factory=list)
    allowed_groups: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignerInput":
        """Create SignerInput from dictionary."""
        return cls(
            account=data["account"],
            scopes=data.get("scopes", 1),
            allowed_contracts=data.get("allowedContracts", []),
            allowed_groups=data.get("allowedGroups", []),
        )


@dataclass
class TransactionInput:
    """Transaction input for t8n.
    
    Simplified transaction format for testing.
    """
    script: str  # hex-encoded script
    signers: List[SignerInput] = field(default_factory=list)
    system_fee: int = 0
    network_fee: int = 0
    valid_until_block: int = 0
    nonce: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransactionInput":
        """Create TransactionInput from dictionary."""
        signers = [
            SignerInput.from_dict(s) for s in data.get("signers", [])
        ]
        return cls(
            script=data["script"],
            signers=signers,
            system_fee=int(data.get("systemFee", 0)),
            network_fee=int(data.get("networkFee", 0)),
            valid_until_block=int(data.get("validUntilBlock", 0)),
            nonce=int(data.get("nonce", 0)),
        )


@dataclass
class Environment:
    """Block environment for execution.
    
    Provides block-level context for transaction execution.
    """
    current_block_number: int = 0
    timestamp: int = 0
    network: int = 860833102  # Neo N3 MainNet magic
    nonce: int = 0
    primary_index: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Environment":
        """Create Environment from dictionary."""
        return cls(
            current_block_number=int(data.get("currentBlockNumber", 0)),
            timestamp=int(data.get("timestamp", 0)),
            network=int(data.get("network", 860833102)),
            nonce=int(data.get("nonce", 0)),
            primary_index=int(data.get("primaryIndex", 0)),
        )


@dataclass
class NotificationOutput:
    """Contract notification in receipt."""
    contract: str  # hex-encoded script hash
    event_name: str
    state: Any  # serialized stack item
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contract": self.contract,
            "eventName": self.event_name,
            "state": self.state,
        }


@dataclass
class Receipt:
    """Transaction execution receipt."""
    tx_hash: str  # hex-encoded
    vm_state: str  # "HALT" or "FAULT"
    gas_consumed: int
    exception: Optional[str] = None
    stack: List[Any] = field(default_factory=list)
    notifications: List[NotificationOutput] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {
            "txHash": self.tx_hash,
            "vmState": self.vm_state,
            "gasConsumed": str(self.gas_consumed),
        }
        if self.exception:
            result["exception"] = self.exception
        if self.stack:
            result["stack"] = self.stack
        if self.notifications:
            result["notifications"] = [n.to_dict() for n in self.notifications]
        return result


@dataclass
class T8NResult:
    """Result of t8n execution."""
    state_root: str  # hex-encoded
    receipts: List[Receipt] = field(default_factory=list)
    gas_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stateRoot": self.state_root,
            "receipts": [r.to_dict() for r in self.receipts],
            "gasUsed": str(self.gas_used),
        }


@dataclass
class T8NOutput:
    """Complete t8n output."""
    result: T8NResult
    alloc: Dict[str, Dict[str, Any]]  # post-state allocation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result": self.result.to_dict(),
            "alloc": self.alloc,
        }
