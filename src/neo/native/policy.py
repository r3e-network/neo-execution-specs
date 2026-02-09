"""Policy contract for network settings."""

from __future__ import annotations
from typing import Any

from neo.types import UInt160
from neo.native.native_contract import NativeContract, CallFlags, StorageItem


# Storage prefixes
PREFIX_BLOCKED_ACCOUNT = 15
PREFIX_FEE_PER_BYTE = 10
PREFIX_EXEC_FEE_FACTOR = 18
PREFIX_STORAGE_PRICE = 19
PREFIX_ATTRIBUTE_FEE = 20

# Default values
DEFAULT_EXEC_FEE_FACTOR = 30
DEFAULT_STORAGE_PRICE = 100000
DEFAULT_FEE_PER_BYTE = 1000
DEFAULT_ATTRIBUTE_FEE = 0

# Maximum values
MAX_EXEC_FEE_FACTOR = 100
MAX_STORAGE_PRICE = 10000000
MAX_ATTRIBUTE_FEE = 10_0000_0000


class PolicyContract(NativeContract):
    """Manages network policy settings.
    
    Controls fees, blocked accounts, and other network parameters.
    Only committee members can modify these settings.
    """
    
    def __init__(self) -> None:
        super().__init__()
    
    @property
    def name(self) -> str:
        return "PolicyContract"
    
    def _register_methods(self) -> None:
        """Register policy methods."""
        super()._register_methods()
        self._register_method("getFeePerByte", self.get_fee_per_byte,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setFeePerByte", self.set_fee_per_byte,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("getExecFeeFactor", self.get_exec_fee_factor,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setExecFeeFactor", self.set_exec_fee_factor,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("getStoragePrice", self.get_storage_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setStoragePrice", self.set_storage_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("isBlocked", self.is_blocked,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("blockAccount", self.block_account,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("unblockAccount", self.unblock_account,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("getAttributeFee", self.get_attribute_fee,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setAttributeFee", self.set_attribute_fee,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
    
    def get_fee_per_byte(self, snapshot: Any) -> int:
        """Get network fee per transaction byte.
        
        Returns:
            Fee in datoshi (1 datoshi = 1e-8 GAS)
        """
        key = self._create_storage_key(PREFIX_FEE_PER_BYTE)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_FEE_PER_BYTE
    
    def set_fee_per_byte(self, engine: Any, value: int) -> None:
        """Set fee per byte. Committee only.
        
        Args:
            engine: Application engine
            value: Fee in datoshi (must be 0-100000000)
        """
        if value < 0 or value > 1_00000000:
            raise ValueError(f"FeePerByte must be between [0, 100000000], got {value}")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        
        key = self._create_storage_key(PREFIX_FEE_PER_BYTE)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)
    
    def get_exec_fee_factor(self, snapshot: Any) -> int:
        """Get execution fee factor.
        
        This multiplier adjusts system fees for transactions.
        
        Returns:
            Execution fee factor
        """
        key = self._create_storage_key(PREFIX_EXEC_FEE_FACTOR)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_EXEC_FEE_FACTOR
    
    def set_exec_fee_factor(self, engine: Any, value: int) -> None:
        """Set execution fee factor. Committee only.
        
        Args:
            engine: Application engine
            value: Fee factor (must be 1-100)
        """
        if value <= 0 or value > MAX_EXEC_FEE_FACTOR:
            raise ValueError(f"ExecFeeFactor must be between [1, {MAX_EXEC_FEE_FACTOR}], got {value}")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        
        key = self._create_storage_key(PREFIX_EXEC_FEE_FACTOR)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)
    
    def get_storage_price(self, snapshot: Any) -> int:
        """Get storage price per byte.
        
        Returns:
            Storage price in datoshi
        """
        key = self._create_storage_key(PREFIX_STORAGE_PRICE)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_STORAGE_PRICE
    
    def set_storage_price(self, engine: Any, value: int) -> None:
        """Set storage price. Committee only.
        
        Args:
            engine: Application engine
            value: Price (must be 1-10000000)
        """
        if value <= 0 or value > MAX_STORAGE_PRICE:
            raise ValueError(f"StoragePrice must be between [1, {MAX_STORAGE_PRICE}], got {value}")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        
        key = self._create_storage_key(PREFIX_STORAGE_PRICE)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)
    
    def is_blocked(self, snapshot: Any, account: UInt160) -> bool:
        """Check if an account is blocked.
        
        Args:
            snapshot: Storage snapshot
            account: Account to check
            
        Returns:
            True if blocked, False otherwise
        """
        key = self._create_storage_key(PREFIX_BLOCKED_ACCOUNT, account.data)
        return snapshot.contains(key)
    
    def block_account(self, engine: Any, account: UInt160) -> bool:
        """Block an account. Committee only.
        
        Blocked accounts cannot send transactions.
        
        Args:
            engine: Application engine
            account: Account to block
            
        Returns:
            True if newly blocked, False if already blocked
        """
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        
        # Cannot block native contracts
        if NativeContract.is_native(account):
            raise ValueError("Cannot block native contract")
        
        key = self._create_storage_key(PREFIX_BLOCKED_ACCOUNT, account.data)
        if engine.snapshot.contains(key):
            return False
        
        engine.snapshot.add(key, StorageItem())
        return True
    
    def unblock_account(self, engine: Any, account: UInt160) -> bool:
        """Unblock an account. Committee only.
        
        Args:
            engine: Application engine
            account: Account to unblock
            
        Returns:
            True if unblocked, False if not blocked
        """
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        
        key = self._create_storage_key(PREFIX_BLOCKED_ACCOUNT, account.data)
        if not engine.snapshot.contains(key):
            return False
        
        engine.snapshot.delete(key)
        return True
    
    def get_attribute_fee(self, snapshot: Any, attribute_type: int) -> int:
        """Get fee for a transaction attribute type.
        
        Args:
            snapshot: Storage snapshot
            attribute_type: Attribute type byte
            
        Returns:
            Fee in datoshi
        """
        key = self._create_storage_key(PREFIX_ATTRIBUTE_FEE, attribute_type)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_ATTRIBUTE_FEE
    
    def set_attribute_fee(self, engine: Any, attribute_type: int, value: int) -> None:
        """Set attribute fee. Committee only.
        
        Args:
            engine: Application engine
            attribute_type: Attribute type byte
            value: Fee (must be <= 10_0000_0000)
        """
        if value < 0 or value > MAX_ATTRIBUTE_FEE:
            raise ValueError(f"AttributeFee must be between [0, {MAX_ATTRIBUTE_FEE}], got {value}")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        
        key = self._create_storage_key(PREFIX_ATTRIBUTE_FEE, attribute_type)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)
    
    def initialize(self, engine: Any) -> None:
        """Initialize policy contract on genesis."""
        fee_key = self._create_storage_key(PREFIX_FEE_PER_BYTE)
        fee_item = StorageItem()
        fee_item.set(DEFAULT_FEE_PER_BYTE)
        engine.snapshot.add(fee_key, fee_item)
        
        exec_key = self._create_storage_key(PREFIX_EXEC_FEE_FACTOR)
        exec_item = StorageItem()
        exec_item.set(DEFAULT_EXEC_FEE_FACTOR)
        engine.snapshot.add(exec_key, exec_item)
        
        storage_key = self._create_storage_key(PREFIX_STORAGE_PRICE)
        storage_item = StorageItem()
        storage_item.set(DEFAULT_STORAGE_PRICE)
        engine.snapshot.add(storage_key, storage_item)
