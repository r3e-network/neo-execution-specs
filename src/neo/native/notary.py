"""Notary native contract for multisignature transaction assistance.

Reference: Neo.SmartContract.Native.Notary
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from neo.hardfork import Hardfork
from neo.native.native_contract import CallFlags, NativeContract, StorageItem
from neo.types import UInt160

# Storage prefixes
PREFIX_DEPOSIT = 1
PREFIX_MAX_NOT_VALID_BEFORE_DELTA = 10

# Default values
DEFAULT_MAX_NOT_VALID_BEFORE_DELTA = 140
DEFAULT_DEPOSIT_DELTA_TILL = 5760

def _write_var_int(buf: bytearray, value: int) -> None:
    """Write a Neo VarInt to buffer."""
    if value < 0xFD:
        buf.append(value)
    elif value <= 0xFFFF:
        buf.append(0xFD)
        buf.extend(value.to_bytes(2, "little"))
    elif value <= 0xFFFFFFFF:
        buf.append(0xFE)
        buf.extend(value.to_bytes(4, "little"))
    else:
        buf.append(0xFF)
        buf.extend(value.to_bytes(8, "little"))

def _read_var_int(data: bytes, offset: int) -> tuple[int, int]:
    """Read a Neo VarInt from data at offset. Returns (value, new_offset)."""
    fb = data[offset]
    offset += 1
    if fb < 0xFD:
        return fb, offset
    elif fb == 0xFD:
        return int.from_bytes(data[offset:offset + 2], "little"), offset + 2
    elif fb == 0xFE:
        return int.from_bytes(data[offset:offset + 4], "little"), offset + 4
    else:
        return int.from_bytes(data[offset:offset + 8], "little"), offset + 8

@dataclass
class Deposit:
    """Notary deposit data."""

    amount: int = 0
    till: int = 0
    
    def serialize(self) -> bytes:
        """Serialize deposit to bytes using VarInt for amount."""
        result = bytearray()
        # Amount as VarInt (Neo serialization format)
        _write_var_int(result, self.amount)
        # Till as 4-byte unsigned LE
        result.extend(self.till.to_bytes(4, 'little'))
        return bytes(result)

    @classmethod
    def deserialize(cls, data: bytes) -> Deposit:
        """Deserialize deposit from bytes."""
        amount, offset = _read_var_int(data, 0)
        till = int.from_bytes(data[offset:offset + 4], 'little')
        return cls(amount=amount, till=till)

class Notary(NativeContract):
    """Notary native contract for multisignature transaction assistance.
    
    Provides functionality for:
    - GAS deposits for notary services
    - Signature verification for notary nodes
    - Managing NotValidBefore delta settings
    """
    
    @property
    def name(self) -> str:
        return "Notary"

    def _contract_activations(self) -> tuple[Any | None, ...]:
        return (Hardfork.HF_ECHIDNA, Hardfork.HF_FAUN)
    
    def _register_methods(self) -> None:
        """Register Notary contract methods."""
        super()._register_methods()
        
        self._register_method("verify", self.verify,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("balanceOf", self.balance_of,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("expirationOf", self.expiration_of,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("lockDepositUntil", self.lock_deposit_until,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("withdraw", self.withdraw,
                            cpu_fee=1 << 15, call_flags=CallFlags.ALL,
                            manifest_parameter_names=["from", "to"])
        self._register_method("getMaxNotValidBeforeDelta", 
                            self.get_max_not_valid_before_delta,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setMaxNotValidBeforeDelta",
                            self.set_max_not_valid_before_delta,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("onNEP17Payment", self.on_nep17_payment,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES,
                            manifest_parameter_names=["from", "amount", "data"])

    def _native_supported_standards(self, context: Any) -> list[str]:
        standards = ["NEP-27"]
        settings, _ = self._hardfork_context(context)
        if settings is not None and self.is_hardfork_enabled(context, Hardfork.HF_FAUN):
            standards.append("NEP-30")
        return standards
    
    def initialize(self, engine: Any) -> None:
        """Initialize Notary contract storage."""
        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            return

        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        item = StorageItem()
        item.set(DEFAULT_MAX_NOT_VALID_BEFORE_DELTA)
        snapshot.put(key, item.value)
    
    def verify(self, engine: Any, signature: bytes) -> bool:
        """Verify notary signature.

        Checks that the transaction was signed by a designated P2P_NOTARY
        node.  Returns False when no notary nodes are designated or the
        signature does not match any of them.
        """
        if signature is None or len(signature) != 64:
            return False

        # Retrieve designated notary nodes for the current block
        try:
            from neo.native.role_management import Role
            snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
            if snapshot is None:
                return False

            block_index = 0
            if hasattr(snapshot, 'persisting_block') and snapshot.persisting_block:
                block_index = getattr(snapshot.persisting_block, 'index', 0)

            # Look up designated notary nodes via RoleManagement
            role_mgmt = NativeContract.get_contract_by_name("RoleManagement")
            if role_mgmt is None:
                return False

            role_mgmt_any = cast(Any, role_mgmt)
            notary_nodes = role_mgmt_any.get_designated_by_role(
                snapshot, Role.P2P_NOTARY, block_index
            )
            if not notary_nodes:
                return False

            # Verify signature against each notary node's public key
            from neo.crypto.ecc.curve import SECP256R1
            from neo.crypto.ecc.signature import verify_signature
            message = getattr(engine.script_container, 'hash', None)
            if message is None:
                return False

            for node in notary_nodes:
                pubkey_bytes = node.encode(compressed=True)
                if verify_signature(message, signature, pubkey_bytes, SECP256R1):
                    return True
        except (ValueError, TypeError, KeyError, AttributeError):
            # Expected failures: malformed keys, missing attributes,
            # invalid signature encoding, missing role management data.
            return False

        return False
    
    def balance_of(self, snapshot: Any, account: UInt160) -> int:
        """Get deposit balance for account."""
        deposit = self._get_deposit(snapshot, account)
        return deposit.amount if deposit else 0

    def expiration_of(self, snapshot: Any, account: UInt160) -> int:
        """Get deposit expiration height for account."""
        deposit = self._get_deposit(snapshot, account)
        return deposit.till if deposit else 0
    
    def lock_deposit_until(
        self,
        engine: Any,
        account: UInt160,
        till: int
    ) -> bool:
        """Lock deposit until specified height.

        Args:
            engine: Application engine
            account: Account to lock deposit for
            till: Block height until which to lock

        Returns:
            True if successful
        """
        # Caller must be the account owner
        if hasattr(engine, 'check_witness') and not engine.check_witness(account):
            raise PermissionError("Account witness required")

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            return False

        deposit = self._get_deposit(snapshot, account)
        if deposit is None:
            return False
        if till < deposit.till:
            return False

        deposit.till = till
        self._put_deposit(snapshot, account, deposit)
        return True
    
    def withdraw(
        self,
        engine: Any,
        from_account: UInt160,
        to_account: UInt160 | None
    ) -> bool:
        """Withdraw deposited GAS.

        Requires witness of ``from_account``.  The deposit must have expired
        (``deposit.till`` <= current persisting block index) before withdrawal
        is allowed.

        Args:
            engine: Application engine
            from_account: Account to withdraw from
            to_account: Account to send to (or from_account if None)

        Returns:
            True if successful
        """
        # Caller must be the account owner
        if hasattr(engine, 'check_witness') and not engine.check_witness(from_account):
            raise PermissionError("Account witness required")

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            return False

        deposit = self._get_deposit(snapshot, from_account)
        if deposit is None:
            return False

        # Deposit must be expired before withdrawal
        block_index = 0
        if hasattr(snapshot, 'persisting_block') and snapshot.persisting_block:
            block_index = getattr(snapshot.persisting_block, 'index', 0)
        if deposit.till > block_index:
            return False

        receive = to_account if to_account else from_account
        amount = deposit.amount

        # Remove deposit first
        self._remove_deposit(snapshot, from_account)

        # Mint GAS to recipient (deposits are virtual; no token-ledger
        # balance exists under self.hash, so we mint instead of transfer)
        if amount > 0:
            gas = NativeContract.get_contract_by_name("GasToken")
            if gas is not None and hasattr(gas, 'mint'):
                gas.mint(engine, receive, amount)

        return True
    
    def get_max_not_valid_before_delta(self, snapshot: Any) -> int:
        """Get maximum NotValidBefore delta."""
        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        value = snapshot.get(key) if snapshot else None
        if value is None:
            return DEFAULT_MAX_NOT_VALID_BEFORE_DELTA
        return int.from_bytes(value, 'little', signed=True) if value else DEFAULT_MAX_NOT_VALID_BEFORE_DELTA

    def set_max_not_valid_before_delta(self, engine: Any, value: int) -> None:
        """Set maximum NotValidBefore delta. Committee only."""
        if value < 1:
            raise ValueError("Value must be positive")
        if hasattr(engine, 'check_committee') and not engine.check_committee():
            raise PermissionError("Committee signature required")

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            return

        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        item = StorageItem()
        item.set(value)
        snapshot.put(key, item.value)
    
    def on_nep17_payment(
        self,
        engine: Any,
        from_account: UInt160,
        amount: int,
        data: Any
    ) -> None:
        """Handle NEP-17 GAS payment for deposit.

        Args:
            engine: Application engine
            from_account: GAS sender
            amount: Amount of GAS sent
            data: [to, till] array
        """
        # Validate caller is GasToken — mandatory check
        gas = NativeContract.get_contract_by_name("GasToken")
        if gas is None:
            raise ValueError("GasToken not found")
        if engine.calling_script_hash != gas.hash:
            raise ValueError("Only GAS transfers are accepted")

        if amount <= 0:
            raise ValueError("Amount must be positive")

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            raise RuntimeError("Snapshot not available")

        # Parse data
        to = from_account
        till = 0

        if isinstance(data, (list, tuple)) and len(data) >= 2:
            if data[0] is not None:
                to = data[0]
            till = int(data[1])

        # Get or create deposit
        deposit = self._get_deposit(snapshot, to)
        if deposit is None:
            deposit = Deposit(amount=0, till=0)

        deposit.amount += amount
        if till > deposit.till:
            deposit.till = till

        self._put_deposit(snapshot, to, deposit)
    
    def _get_deposit(self, snapshot: Any, account: UInt160) -> Deposit | None:
        """Get deposit for account."""
        key = self._create_storage_key(PREFIX_DEPOSIT, account.data)
        value = snapshot.get(key) if snapshot else None
        if value is None:
            return None
        return Deposit.deserialize(value)

    def _put_deposit(self, snapshot: Any, account: UInt160, deposit: Deposit) -> None:
        """Store deposit for account."""
        key = self._create_storage_key(PREFIX_DEPOSIT, account.data)
        snapshot.put(key, deposit.serialize())

    def _remove_deposit(self, snapshot: Any, account: UInt160) -> None:
        """Remove deposit for account."""
        key = self._create_storage_key(PREFIX_DEPOSIT, account.data)
        snapshot.delete(key)
