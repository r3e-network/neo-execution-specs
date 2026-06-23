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

# StackItem binary serialization type bytes (Neo.VM.Types.StackItemType).
_STACKITEM_INTEGER = 0x21
_STACKITEM_STRUCT = 0x41

# Mask used to truncate the parsed Till value to a C# (uint) (32-bit unsigned).
_UINT32_MASK = 0xFFFFFFFF


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


def _int_to_signed_le(value: int) -> bytes:
    """Encode a BigInteger as C# does: minimal signed little-endian, empty for 0."""
    if value == 0:
        return b""
    length = (value.bit_length() + 8) // 8
    return value.to_bytes(length, "little", signed=True)


def _write_var_bytes(buf: bytearray, payload: bytes) -> None:
    """Write VarInt(length) followed by the raw bytes (Neo WriteVarBytes)."""
    _write_var_int(buf, len(payload))
    buf.extend(payload)


def _read_var_bytes(data: bytes, offset: int) -> tuple[bytes, int]:
    """Read VarInt(length)-prefixed bytes from *data* at *offset*."""
    length, offset = _read_var_int(data, offset)
    return data[offset:offset + length], offset + length


@dataclass
class Deposit:
    """Notary deposit data.

    Storage encoding mirrors C# ``Notary.Deposit`` (IInteroperable) written
    through ``BinarySerializer``: a ``Struct`` of two ``Integer`` elements
    ``[Amount, Till]``.  The exact bytes are state-root load-bearing, so the
    layout must match C# exactly (Struct type byte, VarInt count, per-element
    Integer type byte + WriteVarBytes of the value's minimal signed
    little-endian two's-complement bytes, empty when the value is zero).
    """

    amount: int = 0
    till: int = 0

    def serialize(self) -> bytes:
        """Serialize deposit to the C# StackItem ``Struct`` binary format."""
        result = bytearray()
        result.append(_STACKITEM_STRUCT)
        _write_var_int(result, 2)  # element count
        for value in (self.amount, int(self.till) & _UINT32_MASK):
            result.append(_STACKITEM_INTEGER)
            _write_var_bytes(result, _int_to_signed_le(value))
        return bytes(result)

    @classmethod
    def deserialize(cls, data: bytes) -> Deposit:
        """Deserialize a deposit from the C# StackItem ``Struct`` binary format."""
        offset = 0
        type_byte = data[offset]
        offset += 1
        if type_byte != _STACKITEM_STRUCT:
            raise ValueError(f"Expected Struct (0x41), got 0x{type_byte:02x}")
        count, offset = _read_var_int(data, offset)
        if count != 2:
            raise ValueError(f"Expected 2 Deposit fields, got {count}")
        values: list[int] = []
        for _ in range(2):
            elem_type = data[offset]
            offset += 1
            if elem_type != _STACKITEM_INTEGER:
                raise ValueError(f"Expected Integer (0x21), got 0x{elem_type:02x}")
            raw, offset = _read_var_bytes(data, offset)
            values.append(int.from_bytes(raw, "little", signed=True) if raw else 0)
        amount = values[0]
        # C# coerces Till via (uint)@struct[1].GetInteger().
        till = values[1] & _UINT32_MASK
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
    
    def initialize(self, engine: Any, hardfork: Any | None = None) -> None:
        """Initialize Notary contract storage.

        Mirrors C# ``Notary.InitializeAsync`` which only seeds the default
        ``MaxNotValidBeforeDelta`` at the contract's ``ActiveIn`` hardfork
        (HF_Echidna).  When a *hardfork* is supplied it must match HF_Echidna;
        otherwise (lightweight callers/tests that do not thread the hardfork)
        the seed is performed once Echidna is enabled in the context.
        """
        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            return

        if hardfork is not None:
            if hardfork != Hardfork.HF_ECHIDNA:
                return
        elif not self.is_hardfork_enabled(engine, Hardfork.HF_ECHIDNA):
            return

        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        item = StorageItem()
        item.set(DEFAULT_MAX_NOT_VALID_BEFORE_DELTA)
        snapshot.put(key, item.value)

    def on_persist(self, engine: Any) -> None:
        """Deduct notary-assisted fees and mint notary rewards.

        Mirrors C# ``Notary.OnPersistAsync`` (Notary.cs:61-90).  Only runs once
        the Notary contract is active (HF_Echidna+); the native on-persist
        dispatch does not gate on activation, so guard here.
        """
        if not self.is_hardfork_enabled(engine, Hardfork.HF_ECHIDNA):
            return

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        block = getattr(engine, "persisting_block", None)
        if snapshot is None or block is None:
            return

        n_fees = 0
        notaries: Any | None = None
        for tx in getattr(block, "transactions", None) or []:
            attr = self._find_attribute(tx, 0x22)
            if attr is None:
                continue
            if notaries is None:
                notaries = self._get_notary_nodes(engine, snapshot)
            n_keys = int(getattr(attr, "n_keys", 0))
            n_fees += n_keys + 1
            if getattr(tx, "sender", None) == self.hash:
                signers = getattr(tx, "signers", None) or []
                if len(signers) < 2:
                    continue
                payer = getattr(signers[1], "account", None)
                deposit = self._get_deposit(snapshot, payer)
                if deposit is not None:
                    deposit.amount -= int(getattr(tx, "system_fee", 0)) + int(
                        getattr(tx, "network_fee", 0)
                    )
                    if deposit.amount == 0:
                        self._remove_deposit(snapshot, payer)
                    else:
                        self._put_deposit(snapshot, payer, deposit)

        if n_fees == 0 or not notaries:
            return

        attribute_fee = self._get_attribute_fee(engine, 0x22)
        single_reward = (n_fees * attribute_fee) // len(notaries)
        if single_reward <= 0:
            return

        from neo.crypto import hash160
        from neo.smartcontract.syscalls.contract import _create_signature_redeem_script

        gas = NativeContract.get_contract_by_name("GasToken")
        if gas is None or not hasattr(gas, "mint"):
            return
        for notary in notaries:
            pubkey_bytes = notary.encode(compressed=True)
            script = _create_signature_redeem_script(pubkey_bytes)
            recipient = UInt160(hash160(script))
            gas.mint(engine, recipient, single_reward, False)

    def _get_notary_nodes(self, engine: Any, snapshot: Any) -> Any | None:
        """Designated P2P notary nodes for the next block (Ledger.CurrentIndex+1)."""
        from neo.native.role_management import Role

        role_mgmt = NativeContract.get_contract_by_name("RoleManagement")
        if role_mgmt is None:
            return None
        role_mgmt_any = cast(Any, role_mgmt)
        return role_mgmt_any.get_designated_by_role(
            snapshot, Role.P2P_NOTARY, self._current_index(engine) + 1
        )

    def verify(self, engine: Any, signature: bytes) -> bool:
        """Verify notary signature.

        Mirrors C# ``Notary.Verify`` (Notary.cs:112-135):

        * the signature must be exactly 64 bytes;
        * the script container must be a transaction carrying a
          ``NotaryAssisted`` (0x22) attribute;
        * if any signer is the Notary account, its scope must be
          ``WitnessScope.None``;
        * if the transaction sender is the Notary account, there must be
          exactly two signers and the payer (second signer) must hold a
          deposit covering ``networkFee + systemFee``;
        * the signature is checked against the designated P2P notary nodes
          over ``tx.GetSignData(network)``.
        """
        if signature is None or len(signature) != 64:
            return False

        try:
            from neo.native.role_management import Role

            snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
            if snapshot is None:
                return False

            tx = getattr(engine, "script_container", None)
            # Must be a transaction carrying a NotaryAssisted attribute.
            if tx is None or self._find_attribute(tx, 0x22) is None:
                return False

            # Notary signer (if present) must have WitnessScope.None (== 0).
            for signer in getattr(tx, "signers", None) or []:
                if getattr(signer, "account", None) == self.hash:
                    if getattr(signer, "scopes", None) not in (0, None):
                        return False
                    break

            # If the Notary is the sender, the payer deposit must cover fees.
            if getattr(tx, "sender", None) == self.hash:
                signers = getattr(tx, "signers", None) or []
                if len(signers) != 2:
                    return False
                payer = getattr(signers[1], "account", None)
                deposit = self._get_deposit(snapshot, payer)
                fee = int(getattr(tx, "network_fee", 0)) + int(getattr(tx, "system_fee", 0))
                if deposit is None or deposit.amount < fee:
                    return False

            # Look up designated notary nodes via RoleManagement, using the
            # current ledger index + 1 (matches C# GetNotaryNodes).
            role_mgmt = NativeContract.get_contract_by_name("RoleManagement")
            if role_mgmt is None:
                return False
            role_mgmt_any = cast(Any, role_mgmt)
            notary_nodes = role_mgmt_any.get_designated_by_role(
                snapshot, Role.P2P_NOTARY, self._current_index(engine) + 1
            )
            if not notary_nodes:
                return False

            # Verify the signature over tx.GetSignData(network) = SHA256(
            # network_magic_uint32_LE || tx.hash).
            from neo.crypto.ecc.curve import SECP256R1
            from neo.crypto.ecc.signature import verify_signature

            digest = self._tx_sign_data(engine, tx)
            if digest is None:
                return False

            for node in notary_nodes:
                pubkey_bytes = node.encode(compressed=True)
                if verify_signature(digest, signature, pubkey_bytes, SECP256R1):
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

        # Deposit must be valid at least until the next block after the
        # persisting block (mirrors Notary.cs:192).
        if till < self._current_index(engine) + 2:
            return False

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

        receive = to_account if to_account else from_account

        deposit = self._get_deposit(snapshot, from_account)
        if deposit is None:
            return False

        # Deposit must be expired before withdrawal: C# rejects when
        # Ledger.CurrentIndex < deposit.Till (Notary.cs:244).
        if self._current_index(engine) < deposit.till:
            return False

        amount = deposit.amount

        # Remove deposit first (matches C# ordering).
        self._remove_deposit(snapshot, from_account)

        # Transfer the deposited GAS FROM the Notary contract TO the recipient
        # (the Notary holds the real GAS balance; minting would inflate supply).
        # Fault on failure, mirroring C#'s InvalidOperationException.
        gas = NativeContract.get_contract_by_name("GasToken")
        if gas is None or not hasattr(gas, "transfer"):
            raise RuntimeError("GasToken not available for Notary withdrawal")
        if not gas.transfer(engine, self.hash, receive, amount, None):
            raise RuntimeError(f"Transfer to {receive} has failed")

        return True
    
    def get_max_not_valid_before_delta(self, snapshot: Any) -> int:
        """Get maximum NotValidBefore delta."""
        key = self._create_storage_key(PREFIX_MAX_NOT_VALID_BEFORE_DELTA)
        value = snapshot.get(key) if snapshot else None
        if value is None:
            return DEFAULT_MAX_NOT_VALID_BEFORE_DELTA
        return int.from_bytes(value, 'little', signed=True) if value else DEFAULT_MAX_NOT_VALID_BEFORE_DELTA

    def set_max_not_valid_before_delta(self, engine: Any, value: int) -> None:
        """Set maximum NotValidBefore delta. Committee only.

        Bounds-check first, then committee check, then store (Notary.cs:270-280):
        ``value`` must be within ``[ValidatorsCount, maxVUBIncrement / 2]``.
        """
        max_vub_increment = self._max_vub_increment(engine)
        validators_count = self._validators_count(engine)
        if value > max_vub_increment // 2 or value < validators_count:
            raise ValueError(
                f"MaxNotValidBeforeDelta cannot be more than {max_vub_increment // 2} "
                f"or less than {validators_count}"
            )

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
        # Validate caller is GasToken — mandatory check (Notary.cs:148).
        gas = NativeContract.get_contract_by_name("GasToken")
        if gas is None:
            raise ValueError("GasToken not found")
        if engine.calling_script_hash != gas.hash:
            raise ValueError("Only GAS transfers are accepted")

        # `data` must be an array of exactly 2 elements (Notary.cs:149).
        if not isinstance(data, (list, tuple)) or len(data) != 2:
            raise ValueError("`data` parameter should be an array of 2 elements")

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            raise RuntimeError("Snapshot not available")

        # to = from, overridden by data[0] when not Null (Notary.cs:151-152).
        to = from_account
        if data[0] is not None:
            to = data[0] if isinstance(data[0], UInt160) else UInt160(bytes(data[0]))

        # till = (uint)data[1] (Notary.cs:154).
        till = int(data[1]) & _UINT32_MASK

        # allowedChangeTill = (tx.Sender == to) (Notary.cs:155-156).
        tx = getattr(engine, "script_container", None)
        sender = getattr(tx, "sender", None) if tx is not None else None
        allowed_change_till = sender == to

        current_height = self._current_index(engine)
        if till < current_height + 2:
            raise ValueError(
                f"`till` shouldn't be less than the chain's height {current_height + 1} + 1"
            )

        # Load existing deposit (GetAndChange-equivalent; _get_deposit copies).
        deposit = self._get_deposit(snapshot, to)
        if deposit is not None and till < deposit.till:
            raise ValueError(
                f"`till` shouldn't be less than the previous value {deposit.till}"
            )

        if deposit is None:
            fee_per_key = self._get_attribute_fee(engine, 0x22)
            if int(amount) < 2 * fee_per_key:
                raise ValueError(
                    f"first deposit can not be less than {2 * fee_per_key}, got {amount}"
                )
            deposit = Deposit(amount=0, till=0)
            if not allowed_change_till:
                till = current_height + DEFAULT_DEPOSIT_DELTA_TILL
        elif not allowed_change_till:
            till = deposit.till

        deposit.amount += amount
        deposit.till = till  # unconditional (Notary.cs:177)
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

    # ------------------------------------------------------------------
    # Helpers mirroring C# environment accessors
    # ------------------------------------------------------------------

    @staticmethod
    def _find_attribute(tx: Any, attr_type: int) -> Any:
        """Find a transaction attribute by its type code (e.g. 0x22)."""
        for attr in getattr(tx, 'attributes', None) or []:
            if getattr(attr, 'type', None) == attr_type:
                return attr
        return None

    def _current_index(self, engine: Any) -> int:
        """Return Ledger.CurrentIndex(snapshot) with a persisting-block fallback.

        Mirrors C# ``Ledger.CurrentIndex``: the height of the last persisted
        block.  Falls back to the persisting block's index when the Ledger
        contract or its current-block pointer is unavailable (lightweight
        callers/tests).
        """
        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else engine
        ledger = NativeContract.get_contract_by_name("LedgerContract")
        if ledger is not None and hasattr(ledger, "current_index"):
            try:
                return int(ledger.current_index(snapshot))
            except (AttributeError, TypeError, ValueError, KeyError):
                pass
        block = getattr(snapshot, "persisting_block", None)
        if block is not None:
            return int(getattr(block, "index", 0))
        return 0

    @staticmethod
    def _get_network(engine: Any) -> int:
        """Resolve the network magic number from the engine/protocol settings."""
        network = getattr(engine, "network", None)
        if network is None:
            settings = getattr(engine, "protocol_settings", None)
            network = getattr(settings, "network", 0)
        return int(network or 0)

    def _tx_sign_data(self, engine: Any, tx: Any) -> bytes | None:
        """Compute SHA256(network_uint32_LE || tx.hash) (C# GetSignData preimage)."""
        import struct
        from hashlib import sha256

        tx_hash = getattr(tx, "hash", None)
        if callable(tx_hash):
            tx_hash = tx_hash()
        if tx_hash is None:
            return None
        hash_bytes = bytes(getattr(tx_hash, "data", tx_hash))
        if len(hash_bytes) != 32:
            return None
        sign_data = struct.pack("<I", self._get_network(engine) & _UINT32_MASK) + hash_bytes
        return sha256(sign_data).digest()

    def _get_attribute_fee(self, engine: Any, attr_type: int) -> int:
        """Get the attribute fee from PolicyContract (Policy.GetAttributeFeeV1)."""
        policy = NativeContract.get_contract_by_name("PolicyContract")
        if policy is not None and hasattr(policy, "get_attribute_fee"):
            snapshot = engine.snapshot if hasattr(engine, 'snapshot') else engine
            return int(policy.get_attribute_fee(snapshot, attr_type))
        return 0

    def _max_vub_increment(self, engine: Any) -> int:
        """Resolve MaxValidUntilBlockIncrement (Echidna-gated, mirrors C#)."""
        settings = getattr(engine, "protocol_settings", None)
        if self.is_hardfork_enabled(engine, Hardfork.HF_ECHIDNA):
            policy = NativeContract.get_contract_by_name("PolicyContract")
            if policy is not None and hasattr(policy, "get_max_valid_until_block_increment"):
                snapshot = engine.snapshot if hasattr(engine, 'snapshot') else engine
                try:
                    return int(policy.get_max_valid_until_block_increment(snapshot))
                except (AttributeError, TypeError, ValueError, KeyError):
                    pass
        return int(getattr(settings, "max_valid_until_block_increment", 0) or 0)

    @staticmethod
    def _validators_count(engine: Any) -> int:
        """Resolve ProtocolSettings.ValidatorsCount."""
        settings = getattr(engine, "protocol_settings", None)
        count = getattr(settings, "validators_count", None)
        if count is None:
            committee = getattr(settings, "standby_validators", None)
            if committee is not None:
                return len(committee)
            return 0
        return int(count)
