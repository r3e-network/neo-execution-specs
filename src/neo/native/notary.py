"""Notary native contract for multisignature transaction assistance.

Reference: Neo.SmartContract.Native.Notary
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

from neo.types import UInt160
from neo.native.native_contract import NativeContract, CallFlags, StorageKey, StorageItem


# Storage prefixes
PREFIX_DEPOSIT = 1
PREFIX_MAX_NOT_VALID_BEFORE_DELTA = 10

# Default values
DEFAULT_MAX_NOT_VALID_BEFORE_DELTA = 140
DEFAULT_DEPOSIT_DELTA_TILL = 5760


@dataclass
class Deposit:
    """Notary deposit data."""
    amount: int = 0
    till: int = 0
    
    def serialize(self) -> bytes:
        """Serialize deposit to bytes."""
        result = bytearray()
        # Amount as variable-length integer
        amount_bytes = self.amount.to_bytes(8, 'little')
        result.extend(amount_bytes)
        # Till as 4-byte integer
        result.extend(self.till.to_bytes(4, 'little'))
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> Deposit:
        """Deserialize deposit from bytes."""
        amount = int.from_bytes(data[:8], 'little')
        till = int.from_bytes(data[8:12], 'little')
        return cls(amount=amount, till=till)


class Notary(NativeContract):
    """Notary native contract for multisignature transaction assistance.
    
    Provides functionality for:
    - GAS deposits for notary services
    - Signature verification for notary nodes
    - Managing NotValidBefore delta settings
    """
    
    def __init__(self) -> None:
        self._storage: Dict[bytes, StorageItem] = {}
        super().__init__()
    
    @property
    def name(self) -> str:
        return "Notary"
    
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
                            cpu_fee=1 << 15, call_flags=CallFlags.ALL)
        self._register_method("getMaxNotValidBeforeDelta", 
                            self.get_max_not_valid_before_delta,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setMaxNotValidBeforeDelta",
                            self.set_max_not_valid_before_delta,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("onNEP17Payment", self.on_nep17_payment,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
    
    def initialize(self, engine: Any) -> None:
        """Initialize Notary contract storage."""
        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        self._storage[key.key] = StorageItem()
        self._storage[key.key].set(DEFAULT_MAX_NOT_VALID_BEFORE_DELTA)
    
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

            notary_nodes = role_mgmt.get_designated_by_role(
                snapshot, Role.P2P_NOTARY, block_index
            )
            if not notary_nodes:
                return False

            # Verify signature against each notary node's public key
            from neo.crypto.ecc.signature import verify_signature
            from neo.crypto.ecc.curve import SECP256R1
            message = getattr(engine.script_container, 'hash', None)
            if message is None:
                return False

            for node in notary_nodes:
                pubkey_bytes = node.encode(compressed=True)
                if verify_signature(message, signature, pubkey_bytes, SECP256R1):
                    return True
        except Exception:
            pass

        return False
    
    def balance_of(self, snapshot: Any, account: UInt160) -> int:
        """Get deposit balance for account."""
        deposit = self._get_deposit(account)
        return deposit.amount if deposit else 0
    
    def expiration_of(self, snapshot: Any, account: UInt160) -> int:
        """Get deposit expiration height for account."""
        deposit = self._get_deposit(account)
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

        deposit = self._get_deposit(account)
        if deposit is None:
            return False
        if till < deposit.till:
            return False

        deposit.till = till
        self._put_deposit(account, deposit)
        return True
    
    def withdraw(
        self,
        engine: Any,
        from_account: UInt160,
        to_account: Optional[UInt160]
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

        deposit = self._get_deposit(from_account)
        if deposit is None:
            return False

        # Deposit must be expired before withdrawal
        block_index = 0
        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is not None:
            if hasattr(snapshot, 'persisting_block') and snapshot.persisting_block:
                block_index = getattr(snapshot.persisting_block, 'index', 0)
        if deposit.till > block_index:
            return False

        receive = to_account if to_account else from_account
        amount = deposit.amount

        # Remove deposit first
        self._remove_deposit(from_account)

        # Transfer GAS to recipient
        if amount > 0:
            gas = NativeContract.get_contract_by_name("GasToken")
            if gas is not None and hasattr(gas, 'transfer'):
                gas.transfer(engine, self.hash, receive, amount, None)

        return True
    
    def get_max_not_valid_before_delta(self, snapshot: Any) -> int:
        """Get maximum NotValidBefore delta."""
        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        item = self._storage.get(key.key)
        if item is None:
            return DEFAULT_MAX_NOT_VALID_BEFORE_DELTA
        return int(item)
    
    def set_max_not_valid_before_delta(self, engine: Any, value: int) -> None:
        """Set maximum NotValidBefore delta. Committee only."""
        if value < 1:
            raise ValueError("Value must be positive")
        if hasattr(engine, 'check_committee') and not engine.check_committee():
            raise PermissionError("Committee signature required")

        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        if key.key not in self._storage:
            self._storage[key.key] = StorageItem()
        self._storage[key.key].set(value)
    
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
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Parse data
        to = from_account
        till = 0
        
        if isinstance(data, (list, tuple)) and len(data) >= 2:
            if data[0] is not None:
                to = data[0]
            till = int(data[1])
        
        # Get or create deposit
        deposit = self._get_deposit(to)
        if deposit is None:
            deposit = Deposit(amount=0, till=0)
        
        deposit.amount += amount
        if till > deposit.till:
            deposit.till = till
        
        self._put_deposit(to, deposit)
    
    def _get_deposit(self, account: UInt160) -> Optional[Deposit]:
        """Get deposit for account."""
        key = self._create_storage_key(PREFIX_DEPOSIT, account.data)
        item = self._storage.get(key.key)
        if item is None:
            return None
        return Deposit.deserialize(item.value)
    
    def _put_deposit(self, account: UInt160, deposit: Deposit) -> None:
        """Store deposit for account."""
        key = self._create_storage_key(PREFIX_DEPOSIT, account.data)
        self._storage[key.key] = StorageItem(deposit.serialize())
    
    def _remove_deposit(self, account: UInt160) -> None:
        """Remove deposit for account."""
        key = self._create_storage_key(PREFIX_DEPOSIT, account.data)
        if key.key in self._storage:
            del self._storage[key.key]
