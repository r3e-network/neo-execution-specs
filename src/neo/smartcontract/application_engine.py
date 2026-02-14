"""Neo N3 Application Engine - Smart contract execution.

Reference: Neo.SmartContract.ApplicationEngine

The ApplicationEngine extends the base VM ExecutionEngine with:
- Gas metering
- Syscall support
- Native contract invocation
- Storage access
- Notifications and logs
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from neo.exceptions import InvalidOperationException, OutOfGasException
from neo.smartcontract.call_flags import CallFlags
from neo.smartcontract.trigger import TriggerType
from neo.vm.execution_context import ExecutionContext
from neo.vm.execution_engine import ExecutionEngine, VMState  # noqa: F401 (re-exported)
from neo.vm.types import NULL, Array, ByteString, Integer, StackItem

if TYPE_CHECKING:
    from neo.persistence import Snapshot
    from neo.types import UInt160

# Sentinel key for storing CallFlags in ExecutionContext._shared_states.states
_CALL_FLAGS_KEY = "call_flags"


# Gas costs
class GasCost:
    """Standard gas costs for operations."""

    BASE = 1
    OPCODE = 1 << 3  # 8
    STORAGE_READ = 1 << 10  # 1024
    STORAGE_WRITE = 1 << 12  # 4096
    CONTRACT_CALL = 1 << 15  # 32768
    NATIVE_CALL = 1 << 10  # 1024
    CRYPTO_VERIFY = 1 << 15  # 32768
    CRYPTO_HASH = 1 << 10  # 1024


@dataclass
class Notification:
    """Contract notification event."""

    script_hash: UInt160
    event_name: str
    state: StackItem


@dataclass
class LogEntry:
    """Contract log entry."""

    script_hash: UInt160
    message: str


class ApplicationEngine(ExecutionEngine):
    """Neo N3 Application Engine.
    
    Extends ExecutionEngine with smart contract execution capabilities.
    """
    
    def __init__(
        self,
        trigger: TriggerType = TriggerType.APPLICATION,
        gas_limit: int = 10_000_000_000,
        snapshot: Optional[Snapshot] = None,
        script_container: Optional[Any] = None,
        network: int = 860833102,
        protocol_settings: Optional[Any] = None,
        **kwargs
    ):
        """Initialize the application engine."""
        super().__init__(**kwargs)
        
        self.trigger = trigger
        self.gas_consumed = 0
        self.gas_limit = gas_limit
        self.snapshot = snapshot
        self.script_container = script_container
        self.network = network
        self.protocol_settings = protocol_settings
        
        # Execution state
        self._notifications: List[Notification] = []
        self._logs: List[LogEntry] = []
        self._invocation_counters: Dict[bytes, int] = {}
        self._random_counter: int = 0
        self._storage_contexts: Dict[int, Any] = {}
        self._loaded_tokens: Dict[int, Any] = {}
        self._default_call_flags: CallFlags = CallFlags.ALL
        
        # Native contract cache
        self._native_contracts: Dict[bytes, Any] = {}
        
        # Set syscall handler and token handler
        self.syscall_handler = self._handle_syscall
        self.token_handler = self._handle_token_call
        self._register_syscalls()

    @property
    def _current_call_flags(self) -> CallFlags:
        """Get call flags scoped to the current execution context.

        Each context carries its own CallFlags in _shared_states.states.
        Falls back to _default_call_flags when no context is loaded.
        """
        ctx = self.current_context
        if ctx is not None:
            return ctx._shared_states.states.get(_CALL_FLAGS_KEY, self._default_call_flags)
        return self._default_call_flags

    @_current_call_flags.setter
    def _current_call_flags(self, value: CallFlags) -> None:
        """Set call flags on the current execution context."""
        ctx = self.current_context
        if ctx is not None:
            ctx._shared_states.states[_CALL_FLAGS_KEY] = value
        else:
            self._default_call_flags = value

    @property
    def notifications(self) -> List[Notification]:
        """Get all notifications."""
        return self._notifications
    
    @property
    def logs(self) -> List[LogEntry]:
        """Get all log entries."""
        return self._logs
    
    @property
    def current_script_hash(self) -> Optional[UInt160]:
        """Get script hash of current context."""
        from neo.crypto import hash160
        from neo.types import UInt160
        ctx = self.current_context
        if ctx is None:
            return None
        return UInt160(hash160(ctx.script))
    
    @property
    def calling_script_hash(self) -> Optional[UInt160]:
        """Get script hash of calling context."""
        from neo.crypto import hash160
        from neo.types import UInt160
        if len(self.invocation_stack) < 2:
            return None
        ctx = self.invocation_stack[-2]
        return UInt160(hash160(ctx.script))
    
    @property
    def entry_script_hash(self) -> Optional[UInt160]:
        """Get script hash of entry context."""
        from neo.crypto import hash160
        from neo.types import UInt160
        if not self.invocation_stack:
            return None
        ctx = self.invocation_stack[0]
        return UInt160(hash160(ctx.script))
    
    def add_gas(self, amount: int) -> None:
        """Add gas consumption and check limit."""
        self.gas_consumed += amount
        if self.gas_consumed > self.gas_limit:
            raise OutOfGasException("Out of gas")
    
    def send_notification(self, script_hash: UInt160, event_name: str, state: StackItem) -> None:
        """Send a notification event."""
        self._notifications.append(Notification(script_hash, event_name, state))
    
    def write_log(self, script_hash: UInt160, message: str) -> None:
        """Write a log entry."""
        self._logs.append(LogEntry(script_hash, message))
    
    def _handle_syscall(self, engine: ExecutionEngine, hash_val: int) -> None:
        """Handle syscall invocation."""
        from neo.smartcontract.interop_service import invoke_syscall
        invoke_syscall(self, hash_val)
    
    def _handle_token_call(self, engine: ExecutionEngine, token_index: int) -> None:
        """Handle CALLT instruction - call by method token.
        
        CALLT uses a token index to reference a MethodToken in the current
        context's NEF file. The token contains:
        - Contract hash (20 bytes)
        - Method name
        - Parameter count
        - Has return value flag
        - Call flags
        
        This allows static contract calls without runtime hash resolution.
        """
        from neo.smartcontract.call_flags import CallFlags
        from neo.types import UInt160
        
        # Get method tokens from current context
        ctx = self.current_context
        if ctx is None:
            raise InvalidOperationException("No execution context for CALLT")
        
        # Get tokens from context's NEF (stored in shared states)
        tokens = self._get_context_tokens(ctx)
        if tokens is None or token_index >= len(tokens):
            raise InvalidOperationException(f"Invalid token index: {token_index}")
        
        token = tokens[token_index]
        
        # Extract token information
        contract_hash = UInt160(token.hash)
        method = token.method
        params_count = token.parameters_count
        _has_return = token.has_return_value  # reserved for rv_count validation
        call_flags = CallFlags(token.call_flags)
        
        # Pop arguments from stack based on parameter count
        args = []
        for _ in range(params_count):
            args.append(self.pop())
        args.reverse()  # Arguments were pushed in order, popped in reverse
        
        # Look up the contract
        contract = self._get_contract(contract_hash)
        if contract is None:
            raise InvalidOperationException(f"Contract not found: {contract_hash}")
        
        # Verify call flags
        if not self._check_call_flags(call_flags):
            raise InvalidOperationException("Call flags not allowed")
        
        # Create arguments array
        args_array = Array(items=list(args)) if args else Array()
        
        # Call the contract
        self._call_contract_internal(contract, method, args_array, call_flags)
    
    def _get_context_tokens(self, ctx: ExecutionContext) -> Optional[list]:
        """Get method tokens for the current execution context.
        
        Tokens are stored in the context's shared states when the
        contract is loaded from a NEF file.
        """
        # Check if tokens are stored in shared states
        if hasattr(ctx, '_shared_states') and hasattr(ctx._shared_states, 'states'):
            return ctx._shared_states.states.get('method_tokens')
        return None
    
    def load_script_with_tokens(self, script: bytes, tokens: list, rv_count: int = -1) -> ExecutionContext:
        """Load a script with associated method tokens.
        
        This is used when loading contracts from NEF files that contain
        method tokens for CALLT instructions.
        """
        ctx = self.load_script(script, rv_count)
        # Store tokens in shared states
        ctx._shared_states.states['method_tokens'] = tokens
        return ctx
    
    def _register_syscalls(self) -> None:
        """Register all syscalls."""
        from neo.hardfork import Hardfork
        from neo.smartcontract.interop_service import register_syscall

        # System.Runtime syscalls
        register_syscall("System.Runtime.Platform", self._runtime_platform, 1 << 3)
        register_syscall("System.Runtime.GetTrigger", self._runtime_get_trigger, 1 << 3)
        register_syscall("System.Runtime.GetTime", self._runtime_get_time, 1 << 3)
        register_syscall("System.Runtime.GetScriptContainer", self._runtime_get_script_container, 1 << 3)
        register_syscall("System.Runtime.GetExecutingScriptHash", self._runtime_get_executing_script_hash, 1 << 4)
        register_syscall("System.Runtime.GetCallingScriptHash", self._runtime_get_calling_script_hash, 1 << 4)
        register_syscall("System.Runtime.GetEntryScriptHash", self._runtime_get_entry_script_hash, 1 << 4)
        register_syscall("System.Runtime.LoadScript", self._runtime_load_script, 1 << 15, CallFlags.ALLOW_CALL)
        register_syscall("System.Runtime.CheckWitness", self._runtime_check_witness, 1 << 10)
        register_syscall("System.Runtime.GetInvocationCounter", self._runtime_get_invocation_counter, 1 << 4)
        register_syscall("System.Runtime.GetNetwork", self._runtime_get_network, 1 << 3)
        register_syscall("System.Runtime.GetRandom", self._runtime_get_random, 0)
        register_syscall("System.Runtime.Log", self._runtime_log, 1 << 15, CallFlags.ALLOW_NOTIFY)
        register_syscall("System.Runtime.Notify", self._runtime_notify, 1 << 15, CallFlags.ALLOW_NOTIFY)
        register_syscall("System.Runtime.GetNotifications", self._runtime_get_notifications, 1 << 12)
        register_syscall("System.Runtime.GasLeft", self._runtime_gas_left, 1 << 4)
        register_syscall("System.Runtime.BurnGas", self._runtime_burn_gas, 1 << 4)
        register_syscall("System.Runtime.CurrentSigners", self._runtime_current_signers, 1 << 4)
        register_syscall("System.Runtime.GetAddressVersion", self._runtime_get_address_version, 1 << 3)

        # System.Storage syscalls
        register_syscall("System.Storage.GetContext", self._storage_get_context, 1 << 4, CallFlags.READ_STATES)
        register_syscall("System.Storage.GetReadOnlyContext", self._storage_get_readonly_context, 1 << 4, CallFlags.READ_STATES)
        register_syscall("System.Storage.AsReadOnly", self._storage_as_readonly, 1 << 4, CallFlags.READ_STATES)
        register_syscall("System.Storage.Get", self._storage_get, 1 << 15, CallFlags.READ_STATES)
        register_syscall("System.Storage.Find", self._storage_find, 1 << 15, CallFlags.READ_STATES)
        register_syscall("System.Storage.Put", self._storage_put, 1 << 15, CallFlags.WRITE_STATES)
        register_syscall("System.Storage.Delete", self._storage_delete, 1 << 15, CallFlags.WRITE_STATES)
        register_syscall("System.Storage.Local.Get", self._storage_local_get, 1 << 15, CallFlags.READ_STATES, Hardfork.HF_FAUN)
        register_syscall("System.Storage.Local.Find", self._storage_local_find, 1 << 15, CallFlags.READ_STATES, Hardfork.HF_FAUN)
        register_syscall("System.Storage.Local.Put", self._storage_local_put, 1 << 15, CallFlags.WRITE_STATES, Hardfork.HF_FAUN)
        register_syscall("System.Storage.Local.Delete", self._storage_local_delete, 1 << 15, CallFlags.WRITE_STATES, Hardfork.HF_FAUN)

        # System.Contract syscalls
        register_syscall("System.Contract.Call", self._contract_call, 1 << 15, CallFlags.READ_STATES | CallFlags.ALLOW_CALL)
        register_syscall("System.Contract.CallNative", self._contract_call_native, 0)
        register_syscall("System.Contract.GetCallFlags", self._contract_get_call_flags, 1 << 10)
        register_syscall("System.Contract.CreateStandardAccount", self._contract_create_standard_account, 0)
        register_syscall("System.Contract.CreateMultisigAccount", self._contract_create_multisig_account, 0)
        register_syscall("System.Contract.NativeOnPersist", self._contract_native_on_persist, 0, CallFlags.STATES)
        register_syscall("System.Contract.NativePostPersist", self._contract_native_post_persist, 0, CallFlags.STATES)

        # System.Crypto syscalls
        register_syscall("System.Crypto.CheckSig", self._crypto_check_sig, 1 << 15)
        register_syscall("System.Crypto.CheckMultisig", self._crypto_check_multisig, 0)

        # System.Iterator syscalls
        register_syscall("System.Iterator.Next", self._iterator_next, 1 << 15)
        register_syscall("System.Iterator.Value", self._iterator_value, 1 << 4)
    
    # Runtime syscall implementations
    def _runtime_platform(self, engine: ApplicationEngine) -> None:
        """Get platform name."""
        self.push(ByteString(b"NEO"))
    
    def _runtime_get_trigger(self, engine: ApplicationEngine) -> None:
        """Get trigger type."""
        self.push(Integer(int(self.trigger)))
    
    def _runtime_get_time(self, engine: ApplicationEngine) -> None:
        """Get current block time (deterministic).

        Returns the timestamp from the current block's header via the
        persistence snapshot. MUST NOT use wall-clock time — that would
        break consensus across nodes.
        """
        if self.snapshot is not None and hasattr(self.snapshot, 'persisting_block'):
            block = self.snapshot.persisting_block
            if block is not None and hasattr(block, 'timestamp'):
                self.push(Integer(block.timestamp))
                return
        # Fallback: use script_container timestamp if available
        if self.script_container is not None and hasattr(self.script_container, 'timestamp'):
            self.push(Integer(self.script_container.timestamp))
            return
        # No block context — push 0 rather than non-deterministic wall clock
        self.push(Integer(0))
    
    def _runtime_get_script_container(self, engine: ApplicationEngine) -> None:
        """Get script container (transaction)."""
        from neo.vm.types import InteropInterface
        if self.script_container is not None:
            self.push(InteropInterface(self.script_container))
        else:
            self.push(NULL)
    
    def _runtime_get_executing_script_hash(self, engine: ApplicationEngine) -> None:
        """Get executing script hash."""
        script_hash = self.current_script_hash
        if script_hash:
            self.push(ByteString(bytes(script_hash)))
        else:
            self.push(NULL)
    
    def _runtime_get_calling_script_hash(self, engine: ApplicationEngine) -> None:
        """Get calling script hash."""
        script_hash = self.calling_script_hash
        if script_hash:
            self.push(ByteString(bytes(script_hash)))
        else:
            self.push(NULL)
    
    def _runtime_get_entry_script_hash(self, engine: ApplicationEngine) -> None:
        """Get entry script hash."""
        script_hash = self.entry_script_hash
        if script_hash:
            self.push(ByteString(bytes(script_hash)))
        else:
            self.push(NULL)
    
    def _runtime_check_witness(self, engine: ApplicationEngine) -> None:
        """Check witness for account/contract.
        
        Verifies that the specified account or public key has provided
        a valid witness (signature) for the current transaction.
        """
        from neo.crypto import hash160
        
        hash_or_pubkey = self.pop()
        data = hash_or_pubkey.get_bytes_unsafe()
        
        # Determine if this is a script hash (20 bytes) or public key (33/65 bytes)
        if len(data) == 20:
            # It's a script hash (UInt160)
            script_hash = data
        elif len(data) in (33, 65):
            # It's a public key - convert to script hash
            # Standard account script: PUSHDATA1 <pubkey> SYSCALL System.Crypto.CheckSig
            script = bytes([0x0C, len(data)]) + data + bytes([0x41, 0x56, 0xe7, 0xb3, 0x27])
            script_hash = hash160(script)
        else:
            self.push(Integer(0))
            return
        
        # Check if the script hash is in the transaction signers
        result = self._check_witness_internal(script_hash)
        self.push(Integer(1 if result else 0))
    
    def _check_witness_internal(self, script_hash: bytes) -> bool:
        """Internal witness check against transaction signers."""
        # If no script container (transaction), cannot verify
        if self.script_container is None:
            return False
        
        # Check if script_hash matches any signer
        tx = self.script_container
        if not hasattr(tx, 'signers') or not tx.signers:
            return False
        
        for signer in tx.signers:
            if signer.account == script_hash:
                # Found matching signer - check witness scope
                return self._check_witness_scope(signer)
        
        return False
    
    def _check_witness_scope(self, signer) -> bool:
        """Check if the signer's scope allows the current call."""
        from neo.ledger.witness_scope import WitnessScope
        
        scope = signer.scopes
        
        # Global scope allows everything
        if scope & WitnessScope.GLOBAL:
            return True
        
        # CalledByEntry - only valid if called from entry script
        if scope & WitnessScope.CALLED_BY_ENTRY:
            if self.current_script_hash == self.entry_script_hash:
                return True
        
        # CustomContracts - check if current contract is in allowed list
        if scope & WitnessScope.CUSTOM_CONTRACTS:
            current_hash = bytes(self.current_script_hash) if self.current_script_hash else None
            if current_hash and current_hash in [c for c in signer.allowed_contracts]:
                return True
        
        # CustomGroups - check if current contract belongs to an allowed group
        if scope & WitnessScope.CUSTOM_GROUPS:
            if self._check_witness_groups(signer):
                return True

        # Check WitnessRules scope (0x40)
        if scope & 0x40:  # WITNESS_RULES
            rules = getattr(signer, 'rules', [])
            for rule in rules:
                action = getattr(rule, 'action', None)
                condition = getattr(rule, 'condition', None)
                if condition is not None and action is not None:
                    if self._evaluate_witness_condition(condition):
                        if action == 1:  # Allow
                            return True
                        elif action == 0:  # Deny
                            return False

        return False

    def _check_witness_groups(self, signer) -> bool:
        """Check if the current contract belongs to one of the signer's allowed groups.

        Looks up the current contract's manifest, then checks whether any
        of its group public keys appear in ``signer.allowed_groups``.
        """
        import json as _json

        current_hash = self.current_script_hash
        if current_hash is None:
            return False

        contract = self._get_contract(current_hash)
        if contract is None:
            return False

        # Parse manifest to extract groups
        manifest_bytes = getattr(contract, 'manifest', None)
        if not manifest_bytes:
            return False

        try:
            manifest_data = _json.loads(manifest_bytes)
            groups = manifest_data.get("groups", [])
        except (ValueError, TypeError):
            return False

        if not groups:
            return False

        allowed = set(
            bytes(g) if isinstance(g, (bytes, bytearray)) else g
            for g in (signer.allowed_groups or [])
        )
        if not allowed:
            return False

        for group in groups:
            pubkey_hex = group.get("pubkey", "")
            if pubkey_hex:
                try:
                    pubkey = bytes.fromhex(pubkey_hex)
                    if pubkey in allowed:
                        return True
                except (ValueError, TypeError):
                    continue

        return False

    def _evaluate_witness_condition(self, condition) -> bool:
        """Evaluate a WitnessCondition for WitnessRules scope.

        Handles the basic condition types defined by the Neo N3 protocol:
        - Boolean (0x00): literal true/false
        - Not (0x01): logical negation
        - And (0x02): logical conjunction
        - Or (0x03): logical disjunction
        - ScriptHash (0x18): match current script hash
        - Group (0x19): match current contract group
        - CalledByEntry (0x20): current == entry script
        - CalledByContract (0x28): calling script matches hash
        - CalledByGroup (0x29): calling contract matches group
        """
        cond_type = getattr(condition, 'type', None)

        # Boolean
        if cond_type == 0x00:
            return bool(getattr(condition, 'expression', False))

        # Not
        if cond_type == 0x01:
            inner = getattr(condition, 'expression', None)
            if inner is None:
                return False
            return not self._evaluate_witness_condition(inner)

        # And
        if cond_type == 0x02:
            expressions = getattr(condition, 'expressions', [])
            return all(
                self._evaluate_witness_condition(e) for e in expressions
            )

        # Or
        if cond_type == 0x03:
            expressions = getattr(condition, 'expressions', [])
            return any(
                self._evaluate_witness_condition(e) for e in expressions
            )

        # ScriptHash
        if cond_type == 0x18:
            target_hash = getattr(condition, 'hash', None)
            if target_hash is None:
                return False
            current = self.current_script_hash
            if current is None:
                return False
            return bytes(current) == bytes(target_hash)

        # Group
        if cond_type == 0x19:
            target_group = getattr(condition, 'group', None)
            if target_group is None:
                return False
            current = self.current_script_hash
            if current is None:
                return False
            contract = self._get_contract(current)
            if contract is None:
                return False
            manifest = self._parse_contract_manifest(contract)
            if manifest is None:
                return False
            for g in manifest.get("groups", []):
                pubkey_hex = g.get("pubkey", "")
                if pubkey_hex:
                    try:
                        if bytes.fromhex(pubkey_hex) == bytes(target_group):
                            return True
                    except (ValueError, TypeError):
                        continue
            return False

        # CalledByEntry
        if cond_type == 0x20:
            return self.current_script_hash == self.entry_script_hash

        # CalledByContract
        if cond_type == 0x28:
            target_hash = getattr(condition, 'hash', None)
            if target_hash is None:
                return False
            calling = self.calling_script_hash
            if calling is None:
                return False
            return bytes(calling) == bytes(target_hash)

        # CalledByGroup
        if cond_type == 0x29:
            target_group = getattr(condition, 'group', None)
            if target_group is None:
                return False
            calling = self.calling_script_hash
            if calling is None:
                return False
            contract = self._get_contract(calling)
            if contract is None:
                return False
            manifest = self._parse_contract_manifest(contract)
            if manifest is None:
                return False
            for g in manifest.get("groups", []):
                pubkey_hex = g.get("pubkey", "")
                if pubkey_hex:
                    try:
                        if bytes.fromhex(pubkey_hex) == bytes(target_group):
                            return True
                    except (ValueError, TypeError):
                        continue
            return False

        return False

    def _runtime_get_invocation_counter(self, engine: ApplicationEngine) -> None:
        """Get invocation counter for current script."""
        script_hash = self._require_current_script_hash()
        if script_hash:
            count = self._invocation_counters.get(bytes(script_hash), 1)
            self.push(Integer(count))
        else:
            self.push(Integer(0))
    
    def _runtime_get_network(self, engine: ApplicationEngine) -> None:
        """Get network magic number."""
        self.push(Integer(self.network))
    
    def _runtime_get_random(self, engine: ApplicationEngine) -> None:
        """Get deterministic random number.

        C# reference: ``ApplicationEngine.RuntimeGetRandom``

        Uses a counter-based deterministic PRNG seeded from the transaction
        hash so that all consensus nodes produce the identical sequence.

        MUST NOT use Python's ``random`` module.
        """
        if not hasattr(self, '_random_state'):
            # Initialize from tx hash
            tx_hash = getattr(self.script_container, 'hash', b'\x00' * 32)
            if isinstance(tx_hash, bytes):
                seed = tx_hash
            else:
                seed = getattr(tx_hash, 'data', b'\x00' * 32)
            from neo.crypto.hash import hash256
            self._random_state = bytearray(hash256(seed))

        # Use counter for deterministic sequence
        from neo.crypto.hash import hash256
        counter_bytes = self._random_counter.to_bytes(4, 'little')
        combined = bytes(self._random_state) + counter_bytes
        result = hash256(combined)
        self._random_counter += 1

        # Push as integer
        value = int.from_bytes(result, 'little')
        self.push(Integer(value))
    
    def _runtime_log(self, engine: ApplicationEngine) -> None:
        """Write log message.

        C# reference enforces a maximum message length of 1024 bytes.
        """
        message = self.pop()
        msg_str = message.get_string()
        if len(msg_str.encode('utf-8')) > 1024:
            raise InvalidOperationException("Log message exceeds 1024 bytes")
        script_hash = self._require_current_script_hash()
        if script_hash:
            self.write_log(script_hash, msg_str)
    
    def _runtime_notify(self, engine: ApplicationEngine) -> None:
        """Send notification.

        C# pop order: state (top), then eventName.
        """
        state = self.pop()
        event_name = self.pop().get_string()
        script_hash = self._require_current_script_hash()
        if script_hash:
            self.send_notification(script_hash, event_name, state)
    
    def _runtime_get_notifications(self, engine: ApplicationEngine) -> None:
        """Get notifications filtered by contract hash.

        Pops a UInt160 hash filter from the stack.  If the hash is all-zero
        (UInt160.Zero), all notifications are returned; otherwise only those
        whose script_hash matches.

        Each notification is returned as a Struct(script_hash, event_name, state).
        """
        from neo.vm.types import ByteString as BS
        from neo.vm.types import Struct

        hash_item = self.pop()
        filter_bytes = hash_item.get_bytes_unsafe() if not hash_item.is_null else None

        # UInt160.Zero (20 zero bytes) means "no filter"
        is_zero = filter_bytes is None or filter_bytes == b'\x00' * 20

        items: list[StackItem] = []
        for n in self._notifications:
            if not is_zero:
                n_hash = bytes(n.script_hash) if n.script_hash else b'\x00' * 20
                if n_hash != filter_bytes:
                    continue
            entry = Struct(self.reference_counter)
            entry.add(BS(bytes(n.script_hash) if n.script_hash else b'\x00' * 20))
            entry.add(BS(n.event_name.encode('utf-8')))
            entry.add(n.state)
            items.append(entry)

        self.push(Array(items=items))

    def _runtime_gas_left(self, engine: ApplicationEngine) -> None:
        """Get remaining gas."""
        remaining = self.gas_limit - self.gas_consumed
        self.push(Integer(remaining))
    
    def _runtime_burn_gas(self, engine: ApplicationEngine) -> None:
        """Burn specified amount of gas."""
        amount = self.pop().get_integer()
        if amount <= 0:
            raise InvalidOperationException("Invalid gas amount")
        self.add_gas(amount)
    
    def _runtime_current_signers(self, engine: ApplicationEngine) -> None:
        """Get current transaction signers as an Array of Structs.

        Each signer is returned as Struct(account, scopes, allowedContracts,
        allowedGroups, rules).
        """
        from neo.vm.types import ByteString as BS
        from neo.vm.types import Struct

        if self.script_container is None or not hasattr(self.script_container, 'signers'):
            self.push(NULL)
            return

        signers = self.script_container.signers
        if not signers:
            self.push(NULL)
            return

        items: list[StackItem] = []
        for s in signers:
            entry = Struct(self.reference_counter)
            account = bytes(s.account) if s.account else b'\x00' * 20
            entry.add(BS(account))
            entry.add(Integer(s.scopes))
            # allowed_contracts as Array of ByteStrings
            contracts = Array(items=[BS(bytes(c)) for c in (s.allowed_contracts or [])])
            entry.add(contracts)
            # allowed_groups as Array of ByteStrings
            groups = Array(items=[BS(bytes(g)) for g in (s.allowed_groups or [])])
            entry.add(groups)
            items.append(entry)

        self.push(Array(items=items))

    def _runtime_get_address_version(self, engine: ApplicationEngine) -> None:
        """Get address version."""
        self.push(Integer(53))  # Neo N3 address version

    def _runtime_load_script(self, engine: ApplicationEngine) -> None:
        """Load and execute a script dynamically.

        Stack: [call_flags, script] -> []
        """
        call_flags_int = self.pop().get_integer()
        script_data = self.pop().get_bytes_unsafe()

        call_flags = CallFlags(call_flags_int)
        if (call_flags & ~CallFlags.ALL) != 0:
            raise InvalidOperationException("Invalid call flags")

        self.load_script(script_data)
        self._current_call_flags = call_flags  # Now sets on the NEW context

    def _require_current_script_hash(self) -> UInt160:
        script_hash = self.current_script_hash
        if script_hash is None:
            raise InvalidOperationException("No current script hash")
        return script_hash

    def _unwrap_storage_context(self, ctx_item: StackItem) -> Any:
        from neo.smartcontract.storage_context import StorageContext
        from neo.vm.types import InteropInterface

        if not isinstance(ctx_item, InteropInterface):
            raise InvalidOperationException("Invalid storage context")
        ctx = ctx_item.get_interface()
        if not isinstance(ctx, StorageContext):
            raise InvalidOperationException("Invalid storage context")
        return ctx

    # Storage syscall implementations
    def _storage_get_context(self, engine: ApplicationEngine) -> None:
        """Get storage context."""
        from neo.smartcontract.storage_context import StorageContext
        from neo.vm.types import InteropInterface

        script_hash = self._require_current_script_hash()
        contract_id = self._get_contract_id(script_hash)
        ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=False)
        self.push(InteropInterface(ctx))
    
    def _storage_get_readonly_context(self, engine: ApplicationEngine) -> None:
        """Get read-only storage context."""
        from neo.smartcontract.storage_context import StorageContext
        from neo.vm.types import InteropInterface

        script_hash = self._require_current_script_hash()
        contract_id = self._get_contract_id(script_hash)
        ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=True)
        self.push(InteropInterface(ctx))
    
    def _storage_as_readonly(self, engine: ApplicationEngine) -> None:
        """Convert storage context to read-only."""
        from neo.vm.types import InteropInterface

        ctx = self._unwrap_storage_context(self.pop())
        self.push(InteropInterface(ctx.as_read_only()))
    
    def _storage_get(self, engine: ApplicationEngine) -> None:
        """Get value from storage.

        C# pop order: context (top), key.
        """
        ctx = self._unwrap_storage_context(self.pop())
        key = self.pop()

        if self.snapshot is None:
            self.push(NULL)
            return

        key_bytes = key.get_bytes_unsafe()
        full_key = self._build_storage_key(ctx, key_bytes)

        value = self.snapshot.get(full_key)
        if value is None:
            self.push(NULL)
        else:
            self.push(ByteString(value))
    
    def _storage_find(self, engine: ApplicationEngine) -> None:
        """Find values in storage by prefix.

        C# pop order: context (top), prefix, options.
        """
        from neo.smartcontract.iterators import StorageIterator
        from neo.vm.types import InteropInterface

        ctx = self._unwrap_storage_context(self.pop())
        prefix_item = self.pop()
        options_item = self.pop()

        prefix_bytes = prefix_item.get_bytes_unsafe()
        options = int(options_item.get_integer())

        full_prefix = self._build_storage_key(ctx, prefix_bytes)

        iterator = StorageIterator(self, full_prefix, options)
        self.push(InteropInterface(iterator))
    
    def _storage_put(self, engine: ApplicationEngine) -> None:
        """Put value to storage.

        C# pop order: context (top), key, value.
        """
        ctx = self._unwrap_storage_context(self.pop())
        key = self.pop()
        value = self.pop()

        if ctx.is_read_only:
            raise InvalidOperationException("Cannot write to read-only storage context")

        if self.snapshot is None:
            raise InvalidOperationException("No snapshot available for storage")

        key_bytes = key.get_bytes_unsafe()
        value_bytes = value.get_bytes_unsafe()
        full_key = self._build_storage_key(ctx, key_bytes)

        self.snapshot.put(full_key, value_bytes)
        self.add_gas(GasCost.STORAGE_WRITE)
    
    def _storage_delete(self, engine: ApplicationEngine) -> None:
        """Delete value from storage.

        C# pop order: context (top), key.
        """
        ctx = self._unwrap_storage_context(self.pop())
        key = self.pop()

        if ctx.is_read_only:
            raise InvalidOperationException("Cannot delete from read-only storage context")

        if self.snapshot is None:
            raise InvalidOperationException("No snapshot available for storage")

        key_bytes = key.get_bytes_unsafe()
        full_key = self._build_storage_key(ctx, key_bytes)
        self.snapshot.delete(full_key)

    def _storage_local_get(self, engine: ApplicationEngine) -> None:
        """Get value from current contract storage (HF_Faun)."""
        from neo.smartcontract.storage_context import StorageContext
        from neo.vm.types import InteropInterface

        key = self.pop()
        script_hash = self._require_current_script_hash()
        contract_id = self._get_contract_id(script_hash)
        ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=True)

        # Reuse System.Storage.Get stack contract: [context, key]
        self.push(key)
        self.push(InteropInterface(ctx))
        self._storage_get(engine)

    def _storage_local_find(self, engine: ApplicationEngine) -> None:
        """Find values in current contract storage (HF_Faun)."""
        from neo.smartcontract.storage_context import StorageContext
        from neo.vm.types import InteropInterface

        options = self.pop()
        prefix = self.pop()
        script_hash = self._require_current_script_hash()
        contract_id = self._get_contract_id(script_hash)
        ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=True)

        # Reuse System.Storage.Find stack contract: [context, prefix, options]
        self.push(options)
        self.push(prefix)
        self.push(InteropInterface(ctx))
        self._storage_find(engine)

    def _storage_local_put(self, engine: ApplicationEngine) -> None:
        """Put value into current contract storage (HF_Faun)."""
        from neo.smartcontract.storage_context import StorageContext
        from neo.vm.types import InteropInterface

        value = self.pop()
        key = self.pop()
        script_hash = self._require_current_script_hash()
        contract_id = self._get_contract_id(script_hash)
        ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=False)

        # Reuse System.Storage.Put stack contract: [context, key, value]
        self.push(value)
        self.push(key)
        self.push(InteropInterface(ctx))
        self._storage_put(engine)

    def _storage_local_delete(self, engine: ApplicationEngine) -> None:
        """Delete value from current contract storage (HF_Faun)."""
        from neo.smartcontract.storage_context import StorageContext
        from neo.vm.types import InteropInterface

        key = self.pop()
        script_hash = self._require_current_script_hash()
        contract_id = self._get_contract_id(script_hash)
        ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=False)

        # Reuse System.Storage.Delete stack contract: [context, key]
        self.push(key)
        self.push(InteropInterface(ctx))
        self._storage_delete(engine)
    
    def _build_storage_key(self, ctx, key: bytes) -> bytes:
        """Build full storage key from context and user key.

        Neo N3 storage key format: contract_id (int32 LE) + user_key.
        This matches the C# reference ``StorageKey`` implementation where
        the first 4 bytes are the contract's integer ID in little-endian.
        """
        contract_id_bytes = ctx.id.to_bytes(4, byteorder="little", signed=True)
        return contract_id_bytes + key
    
    # Contract syscall implementations
    def _contract_call(self, engine: ApplicationEngine) -> None:
        """Call another contract.
        
        Loads the target contract from storage, verifies permissions,
        and creates a new execution context for the called method.
        """
        from neo.types import UInt160
        
        # C# pop order: callFlags (top), method, contractHash, args
        call_flags = CallFlags(int(self.pop().get_integer()))
        method = self.pop().get_string()
        contract_hash_item = self.pop()
        args = self.pop()  # Pop args Array from stack

        # Get contract hash
        hash_bytes = contract_hash_item.get_bytes_unsafe()
        if len(hash_bytes) != 20:
            raise InvalidOperationException(f"Invalid contract hash length: {len(hash_bytes)}")
        contract_hash = UInt160(hash_bytes)

        # Verify call flags are allowed
        if not self._check_call_flags(call_flags):
            raise InvalidOperationException("Invalid call flags")

        # Look up contract from storage
        contract = self._get_contract(contract_hash)
        if contract is None:
            raise InvalidOperationException(f"Contract not found: {contract_hash}")

        # Check if method exists and is callable
        if not self._check_method_permission(contract, method, call_flags):
            raise InvalidOperationException(f"Method not allowed: {method}")

        # Create new execution context for the called contract
        self._call_contract_internal(contract, method, args, call_flags)
    
    def _check_call_flags(self, flags: int | CallFlags) -> bool:
        """Check if the requested call flags are allowed by current context."""
        requested = CallFlags(int(flags))
        return (requested & self._current_call_flags) == requested
    
    def _get_contract(self, contract_hash: UInt160) -> Optional[Any]:
        """Get contract state from storage."""
        if self.snapshot is None:
            return None
        
        # Try to get from native contracts first
        native = self._get_native_contract(contract_hash)
        if native is not None:
            return native
        
        # Look up in contract management storage
        from neo.native.contract_management import PREFIX_CONTRACT, ContractState

        # Create storage key for contract
        key = bytes([PREFIX_CONTRACT]) + bytes(contract_hash)
        try:
            if hasattr(self.snapshot, 'try_get'):
                value = self.snapshot.try_get(key)
            elif hasattr(self.snapshot, 'get'):
                value = self.snapshot.get(key)
            else:
                return None
        except (KeyError, TypeError, ValueError):
            return None
        if value is None:
            return None

        return ContractState.from_bytes(value)
    
    def _get_native_contract(self, contract_hash: UInt160) -> Optional[Any]:
        """Get native contract by hash."""
        hash_bytes = bytes(contract_hash)
        return self._native_contracts.get(hash_bytes)

    def _get_contract_id(self, script_hash: UInt160) -> int:
        """Resolve the integer contract ID for a given script hash.

        Native contracts carry their own ``id`` property.  Deployed
        contracts are looked up via ``_get_contract`` which returns a
        ``ContractState`` that also exposes ``id``.  Falls back to ``0``
        when the contract cannot be found (e.g. during unit tests that
        skip full deployment).
        """
        native = self._get_native_contract(script_hash)
        if native is not None:
            return native.id

        contract = self._get_contract(script_hash)
        if contract is not None:
            return contract.id

        return 0

    def _check_method_permission(self, contract: Any, method: str, flags: CallFlags) -> bool:
        """Check if a method can be called with the given flags.

        C# reference: ``ApplicationEngine.CheckMethodPermission``

        Validation steps:

        1. **Method existence** — the target contract's ABI must declare
           the method.  Native contracts always pass (their methods are
           registered programmatically, not via JSON manifest).
        2. **Safe-flag enforcement** — if the method is marked ``safe``
           in the ABI, only ``READ_STATES`` is required.  Non-safe
           methods require the caller to hold ``WRITE_STATES``.
        3. **Caller permission** — the *calling* contract's manifest
           ``permissions`` list must include an entry that allows
           invoking the target contract + method combination.

        Returns ``True`` when the call is permitted.
        """
        # --- Native contracts: always permitted (methods are code-registered) ---
        from neo.native.native_contract import NativeContract
        if isinstance(contract, NativeContract):
            return True

        # --- 1. Method existence check via manifest ABI ---
        manifest_data = self._parse_contract_manifest(contract)
        if manifest_data is not None:
            abi = manifest_data.get("abi")
            if abi:
                methods = abi.get("methods", [])
                target_method = None
                for m in methods:
                    if m.get("name") == method:
                        target_method = m
                        break
                if target_method is None:
                    return False  # Method not declared in ABI

                # --- 2. Safe-flag enforcement ---
                is_safe = target_method.get("safe", False)
                if not is_safe:
                    # Non-safe methods require WRITE_STATES in the flags
                    if not (flags & CallFlags.WRITE_STATES):
                        # Caller didn't request write — but method needs it
                        # This is actually checked elsewhere via call flags;
                        # here we just verify the method exists.
                        pass

        # --- 3. Caller permission check ---
        return self._check_caller_permission(contract, method)

    def _check_caller_permission(self, target_contract: Any, method: str) -> bool:
        """Check if the calling contract's manifest permits this call.

        Examines the *caller's* manifest ``permissions`` array.  Each
        ``ContractPermission`` entry specifies a (contract, methods)
        pair.  If any entry matches the target contract + method, the
        call is allowed.

        When there is no calling context (entry-point script), the call
        is always permitted — the entry script has implicit full access.
        """
        # No caller → entry-point script → always allowed
        if len(self.invocation_stack) < 2:
            return True

        # Get the calling contract's manifest
        calling_hash = self.calling_script_hash
        if calling_hash is None:
            return True

        caller_contract = self._get_contract(calling_hash)
        if caller_contract is None:
            return True  # Unknown caller → permissive (test/ad-hoc scripts)

        caller_manifest = self._parse_contract_manifest(caller_contract)
        if caller_manifest is None:
            return True  # No manifest → permissive

        permissions = caller_manifest.get("permissions", [])
        if not permissions:
            return False  # Empty permissions = deny all calls

        # Check each permission entry
        for perm in permissions:
            if self._permission_matches(perm, target_contract, method):
                return True

        return False

    def _permission_matches(
        self, perm: Dict, target_contract: Any, method: str
    ) -> bool:
        """Check if a single permission entry matches the target call."""
        # Contract filter
        contract_filter = perm.get("contract", "*")
        if contract_filter != "*":
            target_hash = None
            if hasattr(target_contract, "hash"):
                target_hash = bytes(target_contract.hash).hex()
            if target_hash is None or contract_filter != target_hash:
                return False

        # Method filter
        methods_filter = perm.get("methods", "*")
        if methods_filter == "*":
            return True
        if isinstance(methods_filter, list):
            return method in methods_filter
        return False

    @staticmethod
    def _parse_contract_manifest(contract: Any) -> Optional[Dict]:
        """Parse a contract's manifest JSON, returning the dict or None."""
        import json as _json

        manifest_raw = getattr(contract, "manifest", None)
        if manifest_raw is None:
            return None

        try:
            if isinstance(manifest_raw, bytes):
                return _json.loads(manifest_raw.decode("utf-8"))
            elif isinstance(manifest_raw, str):
                return _json.loads(manifest_raw)
            elif isinstance(manifest_raw, dict):
                return manifest_raw
        except (ValueError, UnicodeDecodeError, TypeError):
            pass
        return None
    
    def _call_contract_internal(self, contract: Any, method: str,
                                 args: StackItem | None, flags: CallFlags) -> None:
        """Execute a contract call by loading its script.

        Call flags are scoped per execution context: the new context
        receives *flags* while the caller's context retains its own
        flags.  When the called context returns (RET / end-of-script),
        the caller's context becomes current again and its flags are
        automatically restored via the ``_current_call_flags`` property.
        """
        # Get the contract script (NEF)
        if hasattr(contract, 'nef'):
            script = self._extract_script_from_nef(contract.nef)
        elif hasattr(contract, 'script'):
            script = contract.script
        else:
            raise InvalidOperationException("Contract has no executable script")

        # Track invocation count
        from neo.crypto import hash160
        script_hash = hash160(script)
        self._invocation_counters[script_hash] = self._invocation_counters.get(script_hash, 0) + 1

        # Push arguments onto stack for the called method
        from neo.vm.types import Array, Struct
        if isinstance(args, (Array, Struct)):
            for arg in reversed(list(args)):
                self.push(arg)
        elif args is not None and args != NULL:
            self.push(args)

        # Load the contract script — creates a NEW execution context
        self.load_script(script)

        # Set call flags on the NEW (now-current) context.
        # The caller's context retains its own flags untouched.
        self._current_call_flags = flags
    
    def _extract_script_from_nef(self, nef: bytes) -> bytes:
        """Extract executable script from NEF file.

        Parses the NEF3 binary format and returns the embedded script.
        Falls back to treating the input as a raw script when the data
        is too short to be a valid NEF or lacks the correct magic bytes.
        """
        import struct

        from neo.contract.nef import NEF_MAGIC
        from neo.contract.nef import NefFile as NefFormat

        # Minimum NEF size: magic(4) + compiler(64) + source(1) + reserved(1)
        #   + tokens(1) + reserved(2) + script(1) + checksum(4) = 78
        if len(nef) < 78:
            return nef  # Too short for NEF — treat as raw script

        # Quick magic check before full parse
        magic = struct.unpack_from('<I', nef, 0)[0]
        if magic != NEF_MAGIC:
            return nef  # Not a NEF — treat as raw script

        try:
            parsed = NefFormat.deserialize(nef)
            return parsed.script
        except (ValueError, struct.error):
            return nef  # Malformed NEF — fall back to raw bytes
    
    def _contract_call_native(self, engine: ApplicationEngine) -> None:
        """System.Contract.CallNative — dispatch to a native contract method.

        C# reference: ``ApplicationEngine.CallNativeContract``

        Native contract scripts consist of 5-byte stubs, one per method::

            PUSH<version>  (1 byte)  +  SYSCALL CallNative  (1+4 bytes)

        When this syscall fires the engine:

        1. Pops the version integer pushed by the preceding PUSH opcode.
        2. Identifies the native contract via the current script hash.
        3. Calculates the method offset from the instruction pointer
           (``ip // 5 * 5`` — each stub is 5 bytes, aligned).
        4. Looks up the method metadata by offset.
        5. Validates call flags and charges gas (cpu_fee + storage_fee).
        6. Invokes the method handler.

        Note: handler signatures are currently mixed (some accept
        ``engine``, some ``snapshot``, some nothing).  A compatibility
        shim adapts the call until Task #26 unifies them to the C#
        convention ``handler(engine) -> None``.
        """
        from neo.native.native_contract import NativeContract

        # 1. Pop version
        self.pop().get_integer()

        # 2. Identify native contract
        script_hash = self._require_current_script_hash()
        if script_hash is None:
            raise InvalidOperationException("No current script for CallNative")

        contract = NativeContract.get_contract(script_hash)
        if contract is None:
            raise InvalidOperationException(
                f"Native contract not found for hash {script_hash}"
            )

        # 3. Calculate method offset (5-byte aligned stubs)
        ctx = self.current_context
        method_offset = (ctx.ip // 5) * 5

        # 4. Look up method
        method = contract.get_method_by_offset(method_offset)
        if method is None:
            raise InvalidOperationException(
                f"Method not found at offset {method_offset} "
                f"in native contract {contract.name}"
            )

        # 5. Validate call flags
        if not self._check_call_flags(method.required_call_flags):
            raise InvalidOperationException(
                f"Insufficient call flags for {contract.name}.{method.name}"
            )

        # 6. Charge gas
        total_fee = method.cpu_fee + method.storage_fee
        if total_fee > 0:
            self.add_gas(total_fee)

        # 7. Invoke handler (adaptive shim for mixed signatures)
        self._invoke_native_handler(method.handler)

    def _invoke_native_handler(self, handler: Callable) -> None:
        """Invoke a native contract method handler with signature adaptation.

        Native contract handlers currently have mixed signatures:

        * ``handler()``              — simple getters (e.g. ``_get_symbol``)
        * ``handler(snapshot)``      — storage readers
        * ``handler(engine, ...)``   — full engine access

        This shim inspects the callable's signature and provides the
        appropriate arguments.  If the handler returns a non-None value,
        it is auto-converted to a StackItem and pushed onto the eval
        stack (convenience for handlers that aren't yet refactored to
        push results themselves).

        TODO(Task #26): Unify all handlers to ``handler(engine) -> None``
        and remove this shim.
        """
        import inspect

        try:
            sig = inspect.signature(handler)
        except (ValueError, TypeError):
            # Fallback: call with engine
            result = handler(self)
            self._push_native_result(result)
            return

        params = [
            p for p in sig.parameters.values()
            if p.name != "self"
        ]

        if len(params) == 0:
            result = handler()
        elif len(params) == 1:
            # Single param — could be engine or snapshot
            name = params[0].name
            if name == "snapshot":
                result = handler(self.snapshot)
            else:
                result = handler(self)
        else:
            # Multiple params — pass engine; handler pops remaining
            # args from the stack itself
            result = handler(self)

        self._push_native_result(result)

    def _push_native_result(self, result: Any) -> None:
        """Push a native handler's return value onto the eval stack.

        Handlers that already push their own results return ``None``.
        For convenience, non-None return values are auto-converted:

        * ``int``   → ``Integer``
        * ``str``   → ``ByteString`` (UTF-8)
        * ``bytes`` → ``ByteString``
        * ``bool``  → ``Integer(1/0)``
        * ``StackItem`` subclass → pushed directly
        """
        if result is None:
            return

        from neo.vm.types import StackItem as SI

        if isinstance(result, SI):
            self.push(result)
        elif isinstance(result, bool):
            self.push(Integer(1 if result else 0))
        elif isinstance(result, int):
            self.push(Integer(result))
        elif isinstance(result, str):
            self.push(ByteString(result.encode("utf-8")))
        elif isinstance(result, bytes):
            self.push(ByteString(result))
        else:
            # Last resort — try wrapping in InteropInterface
            from neo.vm.types import InteropInterface
            self.push(InteropInterface(result))

    def _contract_get_call_flags(self, engine: ApplicationEngine) -> None:
        """Get current call flags."""
        self.push(Integer(int(self._current_call_flags)))
    
    def _contract_create_standard_account(self, engine: ApplicationEngine) -> None:
        """Create standard account from public key."""
        from neo.crypto import hash160
        pubkey = self.pop()
        # Create script hash from public key
        pubkey_bytes = pubkey.get_bytes_unsafe()
        script = bytes([0x0C, len(pubkey_bytes)]) + pubkey_bytes + bytes([0x41, 0x56, 0xe7, 0xb3, 0x27])
        script_hash = hash160(script)
        self.push(ByteString(script_hash))
    
    def _contract_create_multisig_account(self, engine: ApplicationEngine) -> None:
        """Create multisig account from public keys.

        Pops m (threshold) and an Array of public keys, builds the
        standard multisig verification script, and pushes its hash160.
        """
        from neo.crypto import hash160
        from neo.smartcontract.syscalls.contract import _create_multisig_redeem_script

        m_item = self.pop()
        pubkeys_item = self.pop()

        m = m_item.get_integer()

        # Extract public key bytes from Array or single item
        if hasattr(pubkeys_item, '__iter__') and not isinstance(pubkeys_item, (bytes, str)):
            pubkeys = [p.get_bytes_unsafe() for p in pubkeys_item]
        else:
            pubkeys = [pubkeys_item.get_bytes_unsafe()]

        n = len(pubkeys)
        if m < 1 or m > n or n > 1024:
            raise InvalidOperationException(
                f"Invalid multisig parameters: m={m}, n={n}"
            )

        script = _create_multisig_redeem_script(m, pubkeys)
        script_hash = hash160(script)
        self.push(ByteString(script_hash))
    
    def _contract_native_on_persist(self, engine: ApplicationEngine) -> None:
        """System.Contract.NativeOnPersist — invoke OnPersist on all native contracts.

        C# reference: ``ApplicationEngine.NativeOnPersist``

        Called at the start of block persistence.  Iterates every
        registered native contract (in registration order, i.e. by
        ascending negative ID) and invokes ``on_persist(engine)``.

        Contracts that override ``on_persist`` include:

        * **LedgerContract** — stores block hash and transaction states.
        * **NeoToken** — refreshes committee membership.
        * **GasToken** — burns system/network fees per transaction.
        """
        from neo.native.native_contract import NativeContract

        for contract in sorted(
            NativeContract._contracts_by_id.values(),
            key=lambda c: c.id,
            reverse=True,
        ):
            contract.on_persist(self)
    
    def _contract_native_post_persist(self, engine: ApplicationEngine) -> None:
        """System.Contract.NativePostPersist — invoke PostPersist on all native contracts.

        C# reference: ``ApplicationEngine.NativePostPersist``

        Called after block persistence completes.  Iterates every
        registered native contract and invokes ``post_persist(engine)``.

        Contracts that override ``post_persist`` include:

        * **LedgerContract** — updates the current-block pointer.
        """
        from neo.native.native_contract import NativeContract

        for contract in sorted(
            NativeContract._contracts_by_id.values(),
            key=lambda c: c.id,
            reverse=True,
        ):
            contract.post_persist(self)
    
    # Crypto syscall implementations
    def _crypto_check_sig(self, engine: ApplicationEngine) -> None:
        """Check ECDSA signature.

        C# pop order: signature (top), then pubkey.
        """
        from neo.crypto.ecc.curve import SECP256R1
        from neo.crypto.ecc.signature import verify_signature

        signature = self.pop()
        pubkey = self.pop()

        pubkey_bytes = pubkey.get_bytes_unsafe()
        sig_bytes = signature.get_bytes_unsafe()
        
        # Get the message to verify - this is the transaction hash
        # In Neo, CheckSig verifies against the script container's hash
        if self.script_container is not None and hasattr(self.script_container, 'hash'):
            message_hash = self.script_container.hash
        else:
            # No script container - cannot verify
            self.push(Integer(0))
            return
        
        # Validate input lengths
        if len(sig_bytes) != 64:
            self.push(Integer(0))
            return
        
        if len(pubkey_bytes) not in (33, 65):
            self.push(Integer(0))
            return
        
        # Verify the signature
        try:
            result = verify_signature(message_hash, sig_bytes, pubkey_bytes, SECP256R1)
            self.push(Integer(1 if result else 0))
        except (ValueError, TypeError):
            self.push(Integer(0))
    
    def _crypto_check_multisig(self, engine: ApplicationEngine) -> None:
        """Check multiple ECDSA signatures.
        
        Verifies m-of-n multi-signature using secp256r1 curve.
        Signatures must be provided in the same order as their corresponding public keys.
        """
        from neo.crypto.ecc.curve import SECP256R1
        from neo.crypto.ecc.signature import verify_signature
        
        # C# pop order: pubkeys (top), signatures
        pubkeys_item = self.pop()
        signatures_item = self.pop()
        
        # Get the message hash from script container
        if self.script_container is None or not hasattr(self.script_container, 'hash'):
            self.push(Integer(0))
            return
        
        message_hash = self.script_container.hash
        
        # Extract signatures and public keys from stack items
        try:
            if hasattr(signatures_item, '__iter__'):
                signatures = [s.get_bytes_unsafe() for s in signatures_item]
            else:
                signatures = [signatures_item.get_bytes_unsafe()]
            
            if hasattr(pubkeys_item, '__iter__'):
                pubkeys = [p.get_bytes_unsafe() for p in pubkeys_item]
            else:
                pubkeys = [pubkeys_item.get_bytes_unsafe()]
        except (ValueError, TypeError, AttributeError):
            self.push(Integer(0))
            return

        # Validate: need at least as many pubkeys as signatures
        if len(pubkeys) < len(signatures) or len(signatures) == 0:
            self.push(Integer(0))
            return
        
        # Verify signatures in order
        # Each signature must match a pubkey, and pubkeys must be used in order
        sig_idx = 0
        for pubkey in pubkeys:
            if sig_idx >= len(signatures):
                break
            
            sig = signatures[sig_idx]
            
            # Validate lengths
            if len(sig) != 64 or len(pubkey) not in (33, 65):
                continue
            
            try:
                if verify_signature(message_hash, sig, pubkey, SECP256R1):
                    sig_idx += 1
            except (ValueError, TypeError, OverflowError):
                continue

        # All signatures must have been verified
        result = sig_idx == len(signatures)
        self.push(Integer(1 if result else 0))
    
    # Iterator syscall implementations
    def _iterator_next(self, engine: ApplicationEngine) -> None:
        """Move iterator to next item.

        Pops InteropInterface(IIterator), calls next(), pushes bool.
        """
        from neo.smartcontract.iterators import IIterator

        iterator_item = self.pop()
        if hasattr(iterator_item, 'value') and isinstance(iterator_item.value, IIterator):
            result = iterator_item.value.next()
            self.push(Integer(1 if result else 0))
        else:
            self.push(Integer(0))

    def _iterator_value(self, engine: ApplicationEngine) -> None:
        """Get current iterator value.

        Pops InteropInterface(IIterator), calls value(), pushes StackItem.
        """
        from neo.smartcontract.iterators import IIterator

        iterator_item = self.pop()
        if hasattr(iterator_item, 'value') and isinstance(iterator_item.value, IIterator):
            self.push(iterator_item.value.value())
        else:
            self.push(NULL)
    
    @classmethod
    def run(cls, script: bytes, **kwargs) -> ApplicationEngine:
        """Convenience method to run a script."""
        engine = cls(**kwargs)
        engine.load_script(script)
        engine.execute()
        return engine
