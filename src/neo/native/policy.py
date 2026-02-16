"""Policy contract for network settings."""

from __future__ import annotations
import json
from typing import Any, Iterator

from neo.hardfork import Hardfork
from neo.types import UInt160
from neo.native.native_contract import NativeContract, CallFlags, StorageItem


# Storage prefixes
PREFIX_BLOCKED_ACCOUNT = 15
PREFIX_FEE_PER_BYTE = 10
PREFIX_EXEC_FEE_FACTOR = 18
PREFIX_STORAGE_PRICE = 19
PREFIX_ATTRIBUTE_FEE = 20
PREFIX_MILLISECONDS_PER_BLOCK = 21
PREFIX_MAX_VALID_UNTIL_BLOCK_INCREMENT = 22
PREFIX_MAX_TRACEABLE_BLOCKS = 23
PREFIX_WHITELIST_FEE = 16

# Default values
DEFAULT_EXEC_FEE_FACTOR = 1
DEFAULT_STORAGE_PRICE = 1000
DEFAULT_FEE_PER_BYTE = 20
DEFAULT_ATTRIBUTE_FEE = 0
DEFAULT_EXEC_PICO_FEE_FACTOR = 10000
DEFAULT_MILLISECONDS_PER_BLOCK = 15000
DEFAULT_MAX_VALID_UNTIL_BLOCK_INCREMENT = 5760
DEFAULT_MAX_TRACEABLE_BLOCKS = 2_102_400
REQUIRED_TIME_FOR_RECOVER_FUND_MS = 365 * 24 * 60 * 60 * 1_000

# Maximum values
MAX_EXEC_FEE_FACTOR = 100
MAX_STORAGE_PRICE = 10000000
MAX_ATTRIBUTE_FEE = 10_0000_0000
MAX_MILLISECONDS_PER_BLOCK = 30_000
MAX_MAX_VALID_UNTIL_BLOCK_INCREMENT = 86_400
MAX_MAX_TRACEABLE_BLOCKS = 2_102_400


class _NativeCallEngineProxy:
    """Engine wrapper that overrides calling script hash for native calls."""

    def __init__(self, inner: Any, calling_script_hash: UInt160) -> None:
        self._inner = inner
        self._calling_script_hash = calling_script_hash

    @property
    def calling_script_hash(self) -> UInt160:
        return self._calling_script_hash

    def __getattr__(self, item: str) -> Any:
        return getattr(self._inner, item)


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
        self._register_method(
            "blockAccount",
            self.block_account,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
        )
        self._register_method("getAttributeFee", self.get_attribute_fee, cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method(
            "getBlockedAccounts",
            self.get_blocked_accounts,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method("getExecFeeFactor", self.get_exec_fee_factor, cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method(
            "getExecPicoFeeFactor",
            self.get_exec_pico_fee_factor,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method("getFeePerByte", self.get_fee_per_byte, cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method(
            "getMaxTraceableBlocks",
            self.get_max_traceable_blocks,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_method(
            "getMaxValidUntilBlockIncrement",
            self.get_max_valid_until_block_increment,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_method(
            "getMillisecondsPerBlock",
            self.get_milliseconds_per_block,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_method("getStoragePrice", self.get_storage_price, cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method(
            "getWhitelistFeeContracts",
            self.get_whitelist_fee_contracts,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method("isBlocked", self.is_blocked, cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method(
            "recoverFund",
            self.recover_fund,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            active_in=Hardfork.HF_FAUN,
        )

    def _register_events(self) -> None:
        """Register PolicyContract events."""
        super()._register_events()
        self._register_event(
            "MillisecondsPerBlockChanged",
            [("old", "Integer"), ("new", "Integer")],
            order=0,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_event(
            "WhitelistFeeChanged",
            [
                ("contract", "Hash160"),
                ("method", "String"),
                ("argCount", "Integer"),
                ("fee", "Any"),
            ],
            order=1,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_event(
            "RecoveredFund",
            [("account", "Hash160")],
            order=2,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method(
            "removeWhitelistFeeContract",
            self.remove_whitelist_fee_contract,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method("setAttributeFee", self.set_attribute_fee, cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("setExecFeeFactor", self.set_exec_fee_factor, cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("setFeePerByte", self.set_fee_per_byte, cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method(
            "setMaxTraceableBlocks",
            self.set_max_traceable_blocks,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_method(
            "setMaxValidUntilBlockIncrement",
            self.set_max_valid_until_block_increment,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_method(
            "setMillisecondsPerBlock",
            self.set_milliseconds_per_block,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_method("setStoragePrice", self.set_storage_price, cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method(
            "setWhitelistFeeContract",
            self.set_whitelist_fee_contract,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method("unblockAccount", self.unblock_account, cpu_fee=1 << 15, call_flags=CallFlags.STATES)
    
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

    def get_exec_pico_fee_factor(self, snapshot: Any) -> int:
        """Get execution pico-fee factor."""
        NativeContract.require_hardfork(snapshot, Hardfork.HF_FAUN, "getExecPicoFeeFactor")
        return self.get_exec_fee_factor(snapshot) * DEFAULT_EXEC_PICO_FEE_FACTOR
    
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

    def get_milliseconds_per_block(self, snapshot: Any) -> int:
        """Get target block interval in milliseconds."""
        NativeContract.require_hardfork(snapshot, Hardfork.HF_ECHIDNA, "getMillisecondsPerBlock")
        key = self._create_storage_key(PREFIX_MILLISECONDS_PER_BLOCK)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_MILLISECONDS_PER_BLOCK

    def set_milliseconds_per_block(self, engine: Any, value: int) -> None:
        """Set target block interval in milliseconds. Committee only."""
        NativeContract.require_hardfork(engine, Hardfork.HF_ECHIDNA, "setMillisecondsPerBlock")
        if value <= 0 or value > MAX_MILLISECONDS_PER_BLOCK:
            raise ValueError(
                "MillisecondsPerBlock must be between "
                f"[1, {MAX_MILLISECONDS_PER_BLOCK}], got {value}"
            )
        if not engine.check_committee():
            raise PermissionError("Committee signature required")

        key = self._create_storage_key(PREFIX_MILLISECONDS_PER_BLOCK)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)

    def get_max_valid_until_block_increment(self, snapshot: Any) -> int:
        """Get max valid-until-block increment."""
        NativeContract.require_hardfork(
            snapshot, Hardfork.HF_ECHIDNA, "getMaxValidUntilBlockIncrement"
        )
        key = self._create_storage_key(PREFIX_MAX_VALID_UNTIL_BLOCK_INCREMENT)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_MAX_VALID_UNTIL_BLOCK_INCREMENT

    def set_max_valid_until_block_increment(self, engine: Any, value: int) -> None:
        """Set max valid-until-block increment. Committee only."""
        NativeContract.require_hardfork(
            engine, Hardfork.HF_ECHIDNA, "setMaxValidUntilBlockIncrement"
        )
        if value <= 0 or value > MAX_MAX_VALID_UNTIL_BLOCK_INCREMENT:
            raise ValueError(
                "MaxValidUntilBlockIncrement must be between "
                f"[1, {MAX_MAX_VALID_UNTIL_BLOCK_INCREMENT}], got {value}"
            )
        max_traceable_blocks = self.get_max_traceable_blocks(engine.snapshot)
        if value >= max_traceable_blocks:
            raise ValueError(
                "MaxValidUntilBlockIncrement must be lower than MaxTraceableBlocks "
                f"({value} vs {max_traceable_blocks})"
            )
        if not engine.check_committee():
            raise PermissionError("Committee signature required")

        key = self._create_storage_key(PREFIX_MAX_VALID_UNTIL_BLOCK_INCREMENT)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)

    def get_max_traceable_blocks(self, snapshot: Any) -> int:
        """Get max traceable blocks."""
        NativeContract.require_hardfork(snapshot, Hardfork.HF_ECHIDNA, "getMaxTraceableBlocks")
        key = self._create_storage_key(PREFIX_MAX_TRACEABLE_BLOCKS)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_MAX_TRACEABLE_BLOCKS

    def set_max_traceable_blocks(self, engine: Any, value: int) -> None:
        """Set max traceable blocks. Committee only."""
        NativeContract.require_hardfork(engine, Hardfork.HF_ECHIDNA, "setMaxTraceableBlocks")
        if value <= 0 or value > MAX_MAX_TRACEABLE_BLOCKS:
            raise ValueError(
                f"MaxTraceableBlocks must be between [1, {MAX_MAX_TRACEABLE_BLOCKS}], got {value}"
            )
        old_value = self.get_max_traceable_blocks(engine.snapshot)
        if value > old_value:
            raise ValueError(
                f"MaxTraceableBlocks can not be increased (old {old_value}, new {value})"
            )
        max_valid_until_block_increment = self.get_max_valid_until_block_increment(engine.snapshot)
        if value <= max_valid_until_block_increment:
            raise ValueError(
                "MaxTraceableBlocks must be larger than MaxValidUntilBlockIncrement "
                f"({value} vs {max_valid_until_block_increment})"
            )
        if not engine.check_committee():
            raise PermissionError("Committee signature required")

        key = self._create_storage_key(PREFIX_MAX_TRACEABLE_BLOCKS)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)

    def get_blocked_accounts(self, snapshot: Any) -> Iterator[UInt160]:
        """Get an iterator of blocked accounts."""
        NativeContract.require_hardfork(snapshot, Hardfork.HF_FAUN, "getBlockedAccounts")
        blocked: list[UInt160] = []
        prefix = self._create_storage_key(PREFIX_BLOCKED_ACCOUNT)
        if hasattr(snapshot, "find"):
            for key, _item in snapshot.find(prefix):
                key_bytes = getattr(key, "key", b"")
                if len(key_bytes) >= 21:
                    blocked.append(UInt160(key_bytes[-20:]))
        return iter(blocked)

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

        faun_enabled = NativeContract.is_hardfork_enabled(engine, Hardfork.HF_FAUN)
        neo_token = NativeContract.get_contract_by_name("NeoToken")
        if faun_enabled and neo_token is not None and hasattr(neo_token, "vote_internal"):
            neo_token.vote_internal(engine, account, None)

        entry = StorageItem()
        if faun_enabled:
            entry.set(self._current_time_ms(engine))
        else:
            entry.set(b"")
        engine.snapshot.add(key, entry)
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

    def _resolve_whitelist_method_offset(
        self,
        snapshot: Any,
        contract_hash: UInt160,
        method: str,
        arg_count: int,
    ) -> int:
        contract_management = NativeContract.get_contract_by_name("ContractManagement")
        if contract_management is None or not hasattr(contract_management, "get_contract_state"):
            raise ValueError("Is not a valid contract")

        contract_state = contract_management.get_contract_state(snapshot, contract_hash)
        if contract_state is None:
            raise ValueError("Is not a valid contract")

        try:
            manifest = json.loads(contract_state.manifest.decode("utf-8"))
        except (AttributeError, UnicodeDecodeError, ValueError) as exc:
            raise ValueError(f"Invalid contract manifest for {contract_hash}") from exc

        methods = manifest.get("abi", {}).get("methods", [])
        if not isinstance(methods, list):
            raise ValueError(f"Method {method} with {arg_count} args was not found in {contract_hash}")

        matched_offsets: list[int] = []
        for descriptor in methods:
            if not isinstance(descriptor, dict):
                continue
            if descriptor.get("name") != method:
                continue
            parameters = descriptor.get("parameters")
            if not isinstance(parameters, list) or len(parameters) != arg_count:
                continue
            offset = descriptor.get("offset")
            if not isinstance(offset, int):
                raise ValueError(f"Invalid method offset in manifest for {contract_hash}")
            matched_offsets.append(offset)

        if len(matched_offsets) != 1:
            raise ValueError(f"Method {method} with {arg_count} args was not found in {contract_hash}")

        return matched_offsets[0]

    def _whitelist_key(self, contract_hash: UInt160, method_offset: int):
        return self._create_storage_key(PREFIX_WHITELIST_FEE, contract_hash.data, method_offset)

    def get_whitelist_fee_contracts(self, snapshot: Any) -> Iterator[tuple[bytes, int]]:
        """Get an iterator of configured whitelist fee contracts."""
        NativeContract.require_hardfork(snapshot, Hardfork.HF_FAUN, "getWhitelistFeeContracts")
        rows: list[tuple[bytes, int]] = []
        prefix = self._create_storage_key(PREFIX_WHITELIST_FEE)
        if hasattr(snapshot, "find"):
            for key, item in snapshot.find(prefix):
                key_bytes = getattr(key, "key", b"")
                if len(key_bytes) <= 1:
                    continue
                rows.append((key_bytes[1:], int(item)))
        return iter(rows)

    def set_whitelist_fee_contract(
        self,
        engine: Any,
        contract_hash: UInt160,
        method: str,
        arg_count: int,
        fixed_fee: int,
    ) -> None:
        """Set fixed fee for a whitelisted contract call. Committee only."""
        NativeContract.require_hardfork(engine, Hardfork.HF_FAUN, "setWhitelistFeeContract")
        if fixed_fee < 0:
            raise ValueError("Whitelist fee cannot be negative")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")

        method_offset = self._resolve_whitelist_method_offset(
            engine.snapshot, contract_hash, method, arg_count
        )
        key = self._whitelist_key(contract_hash, method_offset)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(fixed_fee)

    def remove_whitelist_fee_contract(
        self, engine: Any, contract_hash: UInt160, method: str, arg_count: int
    ) -> None:
        """Remove fixed-fee whitelist entry. Committee only."""
        NativeContract.require_hardfork(engine, Hardfork.HF_FAUN, "removeWhitelistFeeContract")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        method_offset = self._resolve_whitelist_method_offset(
            engine.snapshot, contract_hash, method, arg_count
        )
        key = self._whitelist_key(contract_hash, method_offset)
        if hasattr(engine.snapshot, "contains") and not engine.snapshot.contains(key):
            raise ValueError("Whitelist not found")
        engine.snapshot.delete(key)

    def recover_fund(self, engine: Any, account: UInt160, token: UInt160) -> bool:
        """Recover blocked-account funds to Treasury.

        Mirrors Neo v3.9.1 behavior at protocol level:
        - requires (almost) full committee authorization;
        - blocked-account request must be at least 1 year old;
        - token contract must exist and implement NEP-17;
        - transfers full account balance to Treasury.
        """
        NativeContract.require_hardfork(engine, Hardfork.HF_FAUN, "recoverFund")
        if not self._check_almost_full_committee(engine):
            raise PermissionError("Almost full committee signature required")

        key = self._create_storage_key(PREFIX_BLOCKED_ACCOUNT, account.data)
        request_entry = engine.snapshot.get(key)
        if request_entry is None:
            raise ValueError("Request not found.")

        elapsed_time = self._current_time_ms(engine) - int(request_entry)
        if elapsed_time < REQUIRED_TIME_FOR_RECOVER_FUND_MS:
            remaining = REQUIRED_TIME_FOR_RECOVER_FUND_MS - elapsed_time
            remaining_msg = self._format_remaining_time(max(remaining, 0))
            raise ValueError(
                "Request must be signed at least 1 year ago. "
                f"Remaining time: {remaining_msg}."
            )

        native_token = NativeContract.get_contract(token)
        contract_management = NativeContract.get_contract_by_name("ContractManagement")
        contract_state = None
        if contract_management is not None and hasattr(contract_management, "get_contract_state"):
            contract_state = contract_management.get_contract_state(engine.snapshot, token)

        if native_token is None and contract_state is None:
            raise ValueError(f"Contract {token} does not exist.")
        if not self._is_nep17_contract(native_token, contract_state):
            raise ValueError(f"Contract {token} does not implement NEP-17 standard.")

        balance_raw = self._invoke_nep17_method(engine, token, "balanceOf", [account])
        try:
            balance = int(balance_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"NEP-17 balanceOf returned non-integer for contract {token}: {balance_raw!r}"
            ) from exc

        if balance <= 0:
            return False

        treasury = NativeContract.get_contract_by_name("Treasury")
        if treasury is None:
            raise ValueError("Treasury contract is not initialized.")

        transfer_ok = self._invoke_nep17_method(
            engine, token, "transfer", [account, treasury.hash, balance, None]
        )
        if not bool(transfer_ok):
            raise ValueError(
                f"Transfer of {balance} from {account} to {treasury.hash} failed in contract {token}."
            )

        if hasattr(engine, "send_notification"):
            engine.send_notification(self.hash, "RecoveredFund", [account])
        return True

    def _check_almost_full_committee(self, engine: Any) -> bool:
        checker = getattr(engine, "check_almost_committee", None)
        if callable(checker):
            return bool(checker())
        committee_checker = getattr(engine, "check_committee", None)
        return bool(committee_checker()) if callable(committee_checker) else False

    def _current_time_ms(self, engine: Any) -> int:
        getter = getattr(engine, "get_time", None)
        if callable(getter):
            value = getter()
            if isinstance(value, int):
                return value

        snapshot = getattr(engine, "snapshot", None)
        block = getattr(snapshot, "persisting_block", None)
        timestamp = getattr(block, "timestamp", None)
        if isinstance(timestamp, int):
            return timestamp

        block = getattr(engine, "persisting_block", None)
        timestamp = getattr(block, "timestamp", None)
        if isinstance(timestamp, int):
            return timestamp

        script_container = getattr(engine, "script_container", None)
        timestamp = getattr(script_container, "timestamp", None)
        if isinstance(timestamp, int):
            return timestamp

        return 0

    def _format_remaining_time(self, remaining_ms: int) -> str:
        days = remaining_ms // 86_400_000
        hours = (remaining_ms % 86_400_000) // 3_600_000
        minutes = (remaining_ms % 3_600_000) // 60_000
        seconds = (remaining_ms % 60_000) // 1_000
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def _is_nep17_contract(self, native_contract: Any, contract_state: Any) -> bool:
        from neo.native.fungible_token import FungibleToken

        if native_contract is not None and isinstance(native_contract, FungibleToken):
            return True

        if contract_state is None:
            return False
        try:
            manifest = json.loads(contract_state.manifest.decode("utf-8"))
        except (AttributeError, UnicodeDecodeError, ValueError):
            return False

        standards = manifest.get("supportedstandards")
        if not isinstance(standards, list):
            return False
        return any(isinstance(s, str) and s.strip().upper() == "NEP-17" for s in standards)

    def _invoke_nep17_method(
        self,
        engine: Any,
        token_hash: UInt160,
        method: str,
        args: list[Any],
    ) -> Any:
        native = NativeContract.get_contract(token_hash)
        if native is not None:
            method_meta = native.get_method(method)
            if method_meta is None:
                raise ValueError(f"Method {method} does not exist in contract {token_hash}.")
            if method == "balanceOf":
                return method_meta.handler(engine.snapshot, *args)
            if method == "transfer" and args and isinstance(args[0], UInt160):
                proxy = _NativeCallEngineProxy(engine, args[0])
                return method_meta.handler(proxy, *args)
            return method_meta.handler(engine, *args)

        caller = getattr(engine, "call_contract", None)
        if callable(caller):
            return caller(token_hash, method, args)
        raise ValueError(f"Unable to invoke {method} on contract {token_hash}.")

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

        ms_key = self._create_storage_key(PREFIX_MILLISECONDS_PER_BLOCK)
        ms_item = StorageItem()
        ms_item.set(DEFAULT_MILLISECONDS_PER_BLOCK)
        engine.snapshot.add(ms_key, ms_item)

        max_vub_key = self._create_storage_key(PREFIX_MAX_VALID_UNTIL_BLOCK_INCREMENT)
        max_vub_item = StorageItem()
        max_vub_item.set(DEFAULT_MAX_VALID_UNTIL_BLOCK_INCREMENT)
        engine.snapshot.add(max_vub_key, max_vub_item)

        max_trace_key = self._create_storage_key(PREFIX_MAX_TRACEABLE_BLOCKS)
        max_trace_item = StorageItem()
        max_trace_item.set(DEFAULT_MAX_TRACEABLE_BLOCKS)
        engine.snapshot.add(max_trace_key, max_trace_item)
