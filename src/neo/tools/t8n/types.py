"""Type definitions for Neo t8n tool.

Defines input/output data structures for state transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    storage: dict[str, str] = field(default_factory=dict)  # hex key -> hex value
    nef: str | None = None  # hex-encoded NEF
    manifest: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccountState:
        """Create AccountState from dictionary."""
        return cls(
            neo_balance=int(data.get("neoBalance", data.get("neo_balance", 0))),
            gas_balance=int(data.get("gasBalance", data.get("gas_balance", 0))),
            storage=data.get("storage", {}),
            nef=data.get("nef"),
            manifest=data.get("manifest"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {}
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
Alloc = dict[str, AccountState]  # address (hex) -> AccountState


@dataclass
class SignerInput:
    """Transaction signer input."""

    account: str  # hex-encoded UInt160
    scopes: int = 1  # WitnessScope.CALLED_BY_ENTRY
    allowed_contracts: list[str] = field(default_factory=list)
    allowed_groups: list[str] = field(default_factory=list)
    rules: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignerInput:
        """Create SignerInput from dictionary."""
        if not isinstance(data, dict):
            return cls(account="")

        account = data.get("account", "")
        if not isinstance(account, str):
            account = str(account)

        allowed_contracts = data.get("allowedContracts", [])
        if allowed_contracts is None:
            allowed_contracts = []

        allowed_groups = data.get("allowedGroups", [])
        if allowed_groups is None:
            allowed_groups = []

        rules = data.get("rules", [])
        if rules is None:
            rules = []

        return cls(
            account=account,
            scopes=data.get("scopes", 1),
            allowed_contracts=allowed_contracts,
            allowed_groups=allowed_groups,
            rules=rules,
        )


@dataclass
class TransactionInput:
    """Transaction input for t8n.

    Simplified transaction format for testing.
    """

    script: str  # hex-encoded script
    signers: list[SignerInput] = field(default_factory=list)
    system_fee: int = 0
    network_fee: int = 0
    valid_until_block: int = 0
    nonce: int = 0
    parse_error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransactionInput:
        """Create TransactionInput from dictionary."""
        errors: list[str] = []

        if not isinstance(data, dict):
            return cls(script="", parse_error="Transaction entry must be an object")

        script_value = data.get("script")
        if script_value is None:
            errors.append("Transaction missing required script")
            script = ""
        elif isinstance(script_value, str):
            script = script_value
        else:
            errors.append("Transaction script must be a hex string")
            script = str(script_value)

        signers: list[SignerInput] = []
        signers_field = data.get("signers", [])
        if signers_field is None:
            signers_field = []
        if not isinstance(signers_field, list):
            errors.append("Transaction signers must be an array")
        else:
            for signer in signers_field:
                if not isinstance(signer, dict):
                    errors.append("Transaction signer entries must be objects")
                    continue
                signers.append(SignerInput.from_dict(signer))

        return cls(
            script=script,
            signers=signers,
            system_fee=data.get("systemFee", 0),
            network_fee=data.get("networkFee", 0),
            valid_until_block=data.get("validUntilBlock", 0),
            nonce=data.get("nonce", 0),
            parse_error="; ".join(errors) if errors else None,
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
    def from_dict(cls, data: dict[str, Any]) -> Environment:
        """Create Environment from dictionary."""
        return cls(
            current_block_number=int(data.get("currentBlockNumber", 0)),
            timestamp=int(data.get("timestamp", 0)),
            network=int(data.get("network", 860833102)),
            nonce=int(data.get("nonce", 0)),
            primary_index=int(data.get("primaryIndex", 0)),
        )


@dataclass
class Receipt:
    """Transaction execution receipt."""

    tx_hash: str  # hex-encoded
    vm_state: str  # "HALT" or "FAULT"
    gas_consumed: int
    exception: str | None = None
    stack: list[Any] = field(default_factory=list)
    notifications: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "txHash": self.tx_hash,
            "vmState": self.vm_state,
            "gasConsumed": str(self.gas_consumed),
            "stack": self.stack,
            "notifications": [n.to_dict() if hasattr(n, "to_dict") else n for n in self.notifications],
        }
        if self.exception:
            result["exception"] = self.exception
        return result


@dataclass
class T8NResult:
    """Result of t8n execution."""

    state_root: str  # hex-encoded
    receipts: list[Receipt] = field(default_factory=list)
    gas_used: int = 0

    def to_dict(self) -> dict[str, Any]:
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
    alloc: dict[str, dict[str, Any]]  # post-state allocation

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result": self.result.to_dict(),
            "alloc": self.alloc,
        }
