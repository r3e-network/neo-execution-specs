"""Contract Management native contract."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from neo.crypto import hash160
from neo.hardfork import Hardfork
from neo.native.native_contract import CallFlags, NativeContract, StorageItem
from neo.types import UInt160

# Storage prefixes
PREFIX_MINIMUM_DEPLOYMENT_FEE = 20
PREFIX_NEXT_AVAILABLE_ID = 15
PREFIX_CONTRACT = 8
PREFIX_CONTRACT_HASH = 12

# Default minimum deployment fee (10 GAS)
DEFAULT_MINIMUM_DEPLOYMENT_FEE = 10_00000000

# Pico-fee multiplier mirroring C# ApplicationEngine.FeeFactor (ApplicationEngine.cs:74).
# The deployment/update fee is computed in datoshi and multiplied by FeeFactor so it
# is charged in picoGAS, exactly as the C# reference does before AddFee.
FEE_FACTOR = 10000

# Maximum update counter, mirroring C# `ushort.MaxValue` cap in Update.
USHORT_MAX = 0xFFFF

# Basic `_deploy` method that ContractManagement invokes after deploy/update.
# Mirrors C# ContractBasicMethod.Deploy / ContractBasicMethod.DeployPCount.
DEPLOY_METHOD_NAME = "_deploy"
DEPLOY_METHOD_PCOUNT = 2


def _hardfork_enabled(engine: Any, hardfork: Hardfork) -> bool:
    """Return whether *hardfork* is active for the engine.

    Resolves through the engine's own ``is_hardfork_enabled`` when present,
    otherwise falls back to the interop-service helper that evaluates the
    persisting block against the protocol settings.  Engines that carry no
    protocol settings (e.g. unit-test mocks) report every hardfork as
    inactive, which keeps the pre-Aspidochelone / pre-Gorgon code paths
    exercised for those engines.
    """
    method = getattr(engine, "is_hardfork_enabled", None)
    if callable(method):
        try:
            return bool(method(hardfork))
        except TypeError:
            pass
    try:
        from neo.smartcontract.interop_service import _is_hardfork_enabled

        return bool(_is_hardfork_enabled(engine, hardfork))
    except Exception:
        return False


def _compute_nef_checksum(nef: Any) -> int:
    """Compute the NEF checksum, mirroring C# ``NefFile.ComputeChecksum``.

    The checksum is the little-endian uint32 read from the first four bytes
    of ``Hash256`` (double SHA-256) over the serialized NEF minus its own
    trailing 4-byte checksum field.
    """
    import struct

    from neo.crypto import hash256

    raw = nef.to_array()
    return struct.unpack_from("<I", hash256(raw[:-4]), 0)[0]

@dataclass
class ContractState:
    """State of a deployed contract."""

    id: int = 0
    update_counter: int = 0
    hash: UInt160 | None = None
    nef: bytes = b""
    manifest: bytes = b""
    
    def to_bytes(self) -> bytes:
        data = self.id.to_bytes(4, 'little', signed=True)
        data += self.update_counter.to_bytes(2, 'little')
        data += self.hash.data if self.hash else b'\x00' * 20
        data += len(self.nef).to_bytes(4, 'little') + self.nef
        data += len(self.manifest).to_bytes(4, 'little') + self.manifest
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> ContractState:
        state = cls()
        if not data:
            return state
        state.id = int.from_bytes(data[:4], 'little', signed=True)
        state.update_counter = int.from_bytes(data[4:6], 'little')
        state.hash = UInt160(data[6:26])
        nef_len = int.from_bytes(data[26:30], 'little')
        state.nef = data[30:30+nef_len]
        offset = 30 + nef_len
        manifest_len = int.from_bytes(data[offset:offset+4], 'little')
        state.manifest = data[offset+4:offset+4+manifest_len]
        return state

class ContractManagement(NativeContract):
    """Manages contract deployment and updates."""
    
    @property
    def name(self) -> str:
        return "ContractManagement"
    
    def _register_methods(self) -> None:
        """Register contract management methods."""
        super()._register_methods()
        self._register_method("getMinimumDeploymentFee", self.get_minimum_deployment_fee,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setMinimumDeploymentFee", self.set_minimum_deployment_fee,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("getContract", self.get_contract_state,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getContractById", self.get_contract_state_by_id,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getContractHashes", self.get_contract_hashes,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("isContract", self.is_contract,
                            cpu_fee=1 << 14, call_flags=CallFlags.READ_STATES,
                            active_in=Hardfork.HF_ECHIDNA)
        self._register_method("hasMethod", self.has_method,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("deploy", self.deploy_without_data,
                            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
                            manifest_parameter_names=["nefFile", "manifest"])
        self._register_method("deploy", self.deploy,
                            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
                            manifest_parameter_names=["nefFile", "manifest", "data"])
        self._register_method("update", self.update_without_data,
                            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
                            manifest_parameter_names=["nefFile", "manifest"])
        self._register_method("update", self.update,
                            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
                            manifest_parameter_names=["nefFile", "manifest", "data"])
        self._register_method("destroy", self.destroy,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY)

    def _register_events(self) -> None:
        """Register ContractManagement events."""
        super()._register_events()
        self._register_event("Deploy", [("Hash", "Hash160")], order=0)
        self._register_event("Update", [("Hash", "Hash160")], order=1)
        self._register_event("Destroy", [("Hash", "Hash160")], order=2)
    
    def get_minimum_deployment_fee(self, snapshot: Any) -> int:
        """Get minimum deployment fee."""
        key = self._create_storage_key(PREFIX_MINIMUM_DEPLOYMENT_FEE)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_MINIMUM_DEPLOYMENT_FEE
    
    def set_minimum_deployment_fee(self, engine: Any, value: int) -> None:
        """Set minimum deployment fee. Committee only."""
        if value < 0:
            raise ValueError("Value cannot be negative")
        if value > 10_000_000_00000000:
            raise ValueError("Value exceeds maximum deployment fee")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")
        
        key = self._create_storage_key(PREFIX_MINIMUM_DEPLOYMENT_FEE)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(value)
    
    def _get_next_available_id(self, snapshot: Any) -> int:
        """Get and increment the next available contract ID."""
        key = self._create_storage_key(PREFIX_NEXT_AVAILABLE_ID)
        item = snapshot.get_and_change(key)
        value = int(item)
        item.add(1)
        return value
    
    def get_contract_state(
        self,
        context: Any,
        hash: UInt160 | None = None,
    ) -> ContractState | None:
        """Get contract state.

        - ``get_contract_state(context)`` returns this native contract's active state.
        - ``get_contract_state(context, hash)`` resolves a deployed/native contract by hash.
        """
        if hash is None:
            return NativeContract.get_contract_state(self, context)

        snapshot = getattr(context, "snapshot", context)

        native = NativeContract.get_contract(hash)
        if native is not None:
            if not native.is_contract_active(snapshot):
                return None
            return NativeContract.get_contract_state(native, snapshot)

        key = self._create_storage_key(PREFIX_CONTRACT, hash.data)
        item = snapshot.get(key)
        if item is None:
            return None
        return ContractState.from_bytes(item.value)
    
    def get_contract_state_by_id(self, snapshot: Any, id: int) -> ContractState | None:
        """Get a deployed contract by ID."""
        native = NativeContract.get_contract_by_id(id)
        if native is not None:
            if not native.is_contract_active(snapshot):
                return None
            return NativeContract.get_contract_state(native, snapshot)

        # C# encodes the contract id big-endian (StorageKey.Create int overload ->
        # BinaryPrimitives.WriteInt32BigEndian). Pass the id as big-endian bytes so
        # it bypasses the little-endian int branch in StorageKey.create.
        key = self._create_storage_key(PREFIX_CONTRACT_HASH, id.to_bytes(4, "big", signed=True))
        item = snapshot.get(key)
        if item is None:
            return None
        hash = UInt160(item.value)
        return self.get_contract_state(snapshot, hash)

    def get_contract_hashes(self, snapshot: Any) -> Iterator[tuple[int, UInt160]]:
        """Enumerate known contract IDs and hashes."""
        prefix = self._create_storage_key(PREFIX_CONTRACT_HASH)
        rows: list[tuple[int, UInt160]] = []
        if hasattr(snapshot, "find"):
            for key, item in snapshot.find(prefix):
                if not hasattr(key, "key"):
                    continue
                key_bytes = key.key
                if len(key_bytes) < 5:
                    continue
                # C# reads BinaryPrimitives.ReadInt32BigEndian over key[1..].
                contract_id = int.from_bytes(key_bytes[1:5], "big", signed=True)
                if contract_id < 0:  # C# filters .Where(p => p.Id >= 0)
                    continue
                hash_bytes = getattr(item, "value", b"")
                if len(hash_bytes) == 20:
                    rows.append((contract_id, UInt160(hash_bytes)))
        return iter(rows)

    def is_contract(self, snapshot: Any, hash: UInt160) -> bool:
        """Check whether the provided hash belongs to a deployed contract."""
        NativeContract.require_hardfork(snapshot, Hardfork.HF_ECHIDNA, "isContract")
        return self.get_contract_state(snapshot, hash) is not None
    
    def has_method(self, snapshot: Any, hash: UInt160, method: str, pcount: int) -> bool:
        """Check if a contract has a specific method.

        Parses the contract's manifest JSON and inspects the ABI to
        verify that a method with the given *name* and *parameter count*
        actually exists.
        """
        import json as _json

        contract = self.get_contract_state(snapshot, hash)
        if contract is None:
            return False

        # Parse manifest to inspect ABI
        try:
            manifest = _json.loads(contract.manifest.decode('utf-8'))
        except (ValueError, UnicodeDecodeError, AttributeError):
            return False

        abi = manifest.get('abi')
        if not abi:
            return False

        methods = abi.get('methods', [])
        for m in methods:
            if m.get('name') == method:
                params = m.get('parameters', [])
                if len(params) == pcount:
                    return True

        return False

    def _require_call_flags_all(self, engine: Any, method_name: str) -> None:
        """Enforce CallFlags.All for post-Aspidochelone deploy/update.

        Mirrors C# Deploy/Update (ContractManagement.cs:256-262, 329-335):
        once HF_Aspidochelone is active, the calling context must hold the
        full ``CallFlags.All`` flag set, otherwise the operation faults.
        """
        if not _hardfork_enabled(engine, Hardfork.HF_ASPIDOCHELONE):
            return
        flags = getattr(engine, "_current_call_flags", None)
        if flags is None:
            return
        if (int(flags) & int(CallFlags.ALL)) != int(CallFlags.ALL):
            raise ValueError(f"Cannot call {method_name} with the flag {flags}.")

    def _parse_nef(self, nef_file: bytes) -> Any:
        """Parse and validate a NEF file, mirroring C# ``NefFile`` deserialization.

        Validates the magic/token/call-flag structure via ``NefFile.from_array``
        and verifies the trailing checksum equals the computed checksum
        (C# ``NefFile.Deserialize`` -> ``CheckSum != ComputeChecksum`` fault).
        """
        from neo.smartcontract.nef_file import NefFile

        nef = NefFile.from_array(nef_file)
        if nef.checksum != _compute_nef_checksum(nef):
            raise ValueError("CRC verification fail")
        return nef

    def _parse_manifest(self, manifest: bytes) -> tuple[Any, dict]:
        """Parse and validate a manifest, mirroring C# ``ContractManifest.Parse``.

        Enforces the ushort max length (C# ``ContractManifest.Parse`` rejects
        oversized JSON) then runs ``ContractManifest.from_json`` which performs
        the structural validation (name present, no duplicate groups/standards/
        permissions/trusts, empty ``features``).
        """
        import json as _json

        from neo.smartcontract.manifest.contract_manifest import ContractManifest

        if len(manifest) > ContractManifest.MAX_LENGTH:
            raise ValueError("Max length exceeded")
        obj = _json.loads(manifest.decode("utf-8"))
        parsed = ContractManifest.from_json(obj)
        return parsed, obj

    @staticmethod
    def _check_abi(nef: Any, manifest_obj: dict) -> None:
        """Validate that every ABI method offset is within the NEF script.

        Mirrors C# ``Helper.Check(Script, abi)`` which verifies each ABI
        method declares a non-negative offset that lands inside the contract
        script (and a valid event/parameter shape).  The spec ABI carries
        method offsets in its JSON; this enforces the bound that protects the
        deployed manifest from referencing code outside the script body.
        """
        script_len = len(getattr(nef, "script", b""))
        abi = manifest_obj.get("abi") or {}
        for method in abi.get("methods", []):
            offset = method.get("offset", 0)
            if not isinstance(offset, int) or offset < 0 or offset > script_len:
                raise ValueError(
                    f"Method '{method.get('name')}' has an invalid offset {offset}."
                )
        # C# Helper.Check triggers ContractAbi's method/event dictionaries, which
        # reject duplicates: methods keyed by (name, parameter-count) and events
        # keyed by name (ContractAbi.cs:90, Helper.cs:90-91).
        method_keys = [
            (m.get("name"), len(m.get("parameters", []) or []))
            for m in abi.get("methods", [])
        ]
        if len(set(method_keys)) != len(method_keys):
            raise ValueError("Duplicate method (name, parameter count) in ABI.")
        event_names = [e.get("name") for e in abi.get("events", [])]
        if len(set(event_names)) != len(event_names):
            raise ValueError("Duplicate event name in ABI.")

    def deploy_without_data(self, engine: Any, nef_file: bytes, manifest: bytes) -> ContractState:
        """Overload shim for deploy(nef, manifest)."""
        return self.deploy(engine, nef_file, manifest, None)

    def deploy(self, engine: Any, nef_file: bytes, manifest: bytes,
               data: Any = None) -> ContractState:
        """Deploy a new contract.

        Mirrors C# ``ContractManagement.Deploy`` (ContractManagement.cs:254):
        require CallFlags.All post-Aspidochelone, reject empty NEF/manifest,
        charge the per-byte storage fee (or minimum deployment fee) in picoGAS,
        parse+validate the NEF and manifest, compute the contract hash, reject
        blocked or already-deployed hashes, persist the ContractState, run the
        optional ``_deploy`` callback, and emit ``Deploy``.
        """
        self._require_call_flags_all(engine, "Deploy")

        tx = engine.script_container
        if tx is None or not hasattr(tx, "sender"):
            raise ValueError("Deploy requires a transaction script container.")

        if not nef_file:
            raise ValueError("NEF file cannot be empty")
        if not manifest:
            raise ValueError("Manifest cannot be empty")

        # Deployment fee in picoGAS: max(StoragePrice * len, minFee) * FeeFactor.
        storage_price = engine.storage_price
        min_fee = self.get_minimum_deployment_fee(engine.snapshot)
        fee = max(storage_price * (len(nef_file) + len(manifest)), min_fee) * FEE_FACTOR
        engine.add_fee(fee)

        # Parse + validate NEF and manifest (faults on malformed input).
        nef = self._parse_nef(nef_file)
        parsed_manifest, manifest_obj = self._parse_manifest(manifest)
        self._check_abi(nef, manifest_obj)

        # Calculate contract hash from sender, NEF checksum, and manifest name.
        contract_hash = self._calculate_contract_hash(tx.sender, nef_file, manifest)

        # C# ContractManagement.Deploy: the manifest must be valid for the
        # computed hash (every group signature verifies over the hash).
        if not parsed_manifest.is_valid(getattr(engine, "limits", None), contract_hash):
            raise ValueError(f"Invalid Manifest: {contract_hash}")

        # Reject blocked hashes (Policy.IsBlocked) when Policy is registered.
        policy = NativeContract.get_contract_by_name("PolicyContract")
        if policy is not None and policy.is_blocked(engine.snapshot, contract_hash):
            raise ValueError(f"The contract {contract_hash} has been blocked.")

        # Check if contract already exists.
        key = self._create_storage_key(PREFIX_CONTRACT, contract_hash.data)
        if engine.snapshot.contains(key):
            raise ValueError(f"Contract already exists: {contract_hash}")

        # Create contract state.
        contract = ContractState(
            id=self._get_next_available_id(engine.snapshot),
            update_counter=0,
            hash=contract_hash,
            nef=nef_file,
            manifest=manifest
        )

        # Store contract.
        engine.snapshot.add(key, StorageItem(contract.to_bytes()))
        # C# encodes the contract id big-endian for Prefix_ContractHash.
        hash_key = self._create_storage_key(
            PREFIX_CONTRACT_HASH, contract.id.to_bytes(4, "big", signed=True)
        )
        engine.snapshot.add(hash_key, StorageItem(contract_hash.data))

        # Invoke the optional `_deploy` callback and emit the Deploy event.
        self._on_deploy(engine, contract, manifest_obj, data, update=False)

        return contract

    def _on_deploy(
        self,
        engine: Any,
        contract: ContractState,
        manifest_obj: dict,
        data: Any,
        update: bool,
    ) -> None:
        """Dispatch the contract's `_deploy` method then emit Deploy/Update.

        Mirrors C# ``ContractManagement.OnDeployAsync`` (ContractManagement.cs:63):
        when the manifest's ABI declares ``_deploy`` with 2 parameters, call it
        on the deployed contract with ``(data, update)`` and ``CallFlags.All``;
        always emit the ``Deploy`` (first deploy) or ``Update`` notification.
        """
        if self._manifest_declares_deploy(manifest_obj):
            invoke = getattr(engine, "call_from_native_contract", None)
            if callable(invoke):
                invoke(self.hash, contract.hash, DEPLOY_METHOD_NAME, data, update)

        event = "Update" if update else "Deploy"
        engine.send_notification(self.hash, event, [contract.hash])

    @staticmethod
    def _manifest_declares_deploy(manifest_obj: dict) -> bool:
        """Return whether the manifest ABI declares the 2-arg `_deploy` method."""
        abi = manifest_obj.get("abi") or {}
        for method in abi.get("methods", []):
            if (
                method.get("name") == DEPLOY_METHOD_NAME
                and len(method.get("parameters", [])) == DEPLOY_METHOD_PCOUNT
            ):
                return True
        return False


    def _calculate_contract_hash(self, sender: UInt160, nef: bytes,
                                  manifest: bytes) -> UInt160:
        """Calculate contract hash from sender, NEF checksum, and name.

        Matches C# Helper.GetContractHash: builds a script with
        ABORT + PUSHDATA1(sender) + PUSHDATA1(nef_checksum_le) + PUSHDATA1(name_utf8)
        then hashes it with Hash160.
        """
        import json
        import struct

        from neo.vm.opcode import OpCode

        # Parse manifest to get name
        manifest_obj = json.loads(manifest.decode('utf-8'))
        name = manifest_obj.get('name', '')

        # NEF checksum is the last 4 bytes of the serialized NEF
        if len(nef) >= 4:
            nef_checksum = struct.unpack_from('<I', nef, len(nef) - 4)[0]
        else:
            nef_checksum = 0

        # Build script: ABORT + PUSHDATA1(sender) + PUSHDATA1(checksum) + PUSHDATA1(name)
        script = bytearray()
        script.append(OpCode.ABORT)

        # Push sender (20 bytes)
        sender_bytes = sender.data if hasattr(sender, 'data') else bytes(sender)
        script.append(OpCode.PUSHDATA1)
        script.append(len(sender_bytes))
        script.extend(sender_bytes)

        # Push nef checksum (4 bytes LE)
        checksum_bytes = nef_checksum.to_bytes(4, 'little')
        script.append(OpCode.PUSHDATA1)
        script.append(len(checksum_bytes))
        script.extend(checksum_bytes)

        # Push name (UTF-8)
        name_bytes = name.encode('utf-8')
        script.append(OpCode.PUSHDATA1)
        script.append(len(name_bytes))
        script.extend(name_bytes)

        return UInt160(hash160(bytes(script)))

    def update_without_data(
        self, engine: Any, nef_file: bytes | None, manifest: bytes | None
    ) -> None:
        """Overload shim for update(nef, manifest)."""
        self.update(engine, nef_file, manifest, None)
    
    def update(self, engine: Any, nef_file: bytes | None,
               manifest: bytes | None, data: Any = None) -> None:
        """Update an existing contract.

        Mirrors C# ``ContractManagement.Update`` (ContractManagement.cs:327):
        require CallFlags.All post-Aspidochelone, reject the both-null case,
        charge the per-byte storage fee in picoGAS, fetch the calling
        contract, enforce the ushort update-counter cap, validate the new NEF
        and manifest (name immutability + structural validity), clean the
        whitelist, bump the counter, run the optional ``_deploy`` callback, and
        emit ``Update``.
        """
        self._require_call_flags_all(engine, "Update")

        if nef_file is None and manifest is None:
            raise ValueError("NEF and manifest cannot both be null")

        # Storage fee in picoGAS over the supplied NEF + manifest lengths.
        nef_len = len(nef_file) if nef_file is not None else 0
        manifest_len = len(manifest) if manifest is not None else 0
        engine.add_fee(engine.storage_price * FEE_FACTOR * (nef_len + manifest_len))

        # Get calling contract.
        calling_hash = engine.calling_script_hash
        key = self._create_storage_key(PREFIX_CONTRACT, calling_hash.data)
        item = engine.snapshot.get_and_change(key)
        if item is None:
            raise ValueError(f"Contract does not exist: {calling_hash}")

        contract = ContractState.from_bytes(item.value)
        if contract.update_counter == USHORT_MAX:
            raise ValueError("The contract reached the maximum number of updates.")

        new_nef = None
        # Update NEF if provided.
        if nef_file is not None:
            if not nef_file:
                raise ValueError("NEF file cannot be empty")
            new_nef = self._parse_nef(nef_file)
            contract.nef = nef_file

        # Clean whitelist (with the old manifest information) before swapping it.
        policy = NativeContract.get_contract_by_name("PolicyContract")
        if policy is not None:
            policy.clean_whitelist(engine, contract)

        # Update manifest if provided.
        manifest_obj = None
        if manifest is not None:
            if not manifest:
                raise ValueError("Manifest cannot be empty")
            parsed_new, manifest_obj = self._parse_manifest(manifest)
            old_name = self._manifest_name(contract.manifest)
            if parsed_new.name != old_name:
                raise ValueError("The name of the contract can't be changed.")
            # C# ContractManagement.Update: manifestNew.IsValid(limits, contract.Hash).
            if not parsed_new.is_valid(getattr(engine, "limits", None), contract.hash):
                raise ValueError(f"Invalid Manifest: {contract.hash}")
            contract.manifest = manifest

        # Re-run the ABI/script consistency check over the (possibly) new pair.
        if new_nef is None:
            new_nef = self._parse_nef(contract.nef)
        if manifest_obj is None:
            manifest_obj = self._manifest_obj(contract.manifest)
        self._check_abi(new_nef, manifest_obj)

        # Increase update counter and persist.
        contract.update_counter += 1
        item.value = contract.to_bytes()

        # Invoke the optional `_deploy` callback (update=True) + emit Update.
        self._on_deploy(engine, contract, manifest_obj, data, update=True)

    @staticmethod
    def _manifest_obj(manifest: bytes) -> dict:
        """Decode a stored manifest blob into its JSON object."""
        import json as _json

        try:
            return _json.loads(manifest.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, AttributeError):
            return {}

    @classmethod
    def _manifest_name(cls, manifest: bytes) -> str:
        """Read the ``name`` field from a stored manifest blob."""
        return cls._manifest_obj(manifest).get("name", "")

    def destroy(self, engine: Any) -> None:
        """Destroy the calling contract.

        Mirrors C# ``ContractManagement.DestroyInternal`` (ContractManagement.cs:405)
        with the HF_Gorgon V0/V1 split: post-Gorgon (V1) the contract account is
        blocked and its whitelist cleaned *before* erasing the contract state and
        storage; pre-Gorgon (V0) the blocking/cleaning happens *after* erasure.
        """
        block_before_erase = _hardfork_enabled(engine, Hardfork.HF_GORGON)

        calling_hash = engine.calling_script_hash
        key = self._create_storage_key(PREFIX_CONTRACT, calling_hash.data)
        item = engine.snapshot.get(key)
        if item is None:
            return

        contract = ContractState.from_bytes(item.value)
        policy = NativeContract.get_contract_by_name("PolicyContract")

        if block_before_erase:
            self._block_and_clean(engine, policy, calling_hash, contract)

        # Delete contract.
        engine.snapshot.delete(key)
        # C# encodes the contract id big-endian for Prefix_ContractHash.
        hash_key = self._create_storage_key(
            PREFIX_CONTRACT_HASH, contract.id.to_bytes(4, "big", signed=True)
        )
        engine.snapshot.delete(hash_key)

        # Delete contract storage.
        engine.snapshot.delete_contract_storage(contract.id)

        if not block_before_erase:
            self._block_and_clean(engine, policy, calling_hash, contract)

        engine.send_notification(self.hash, "Destroy", [calling_hash])

    @staticmethod
    def _block_and_clean(
        engine: Any, policy: Any, hash: UInt160, contract: ContractState
    ) -> None:
        """Block the contract account and clean its whitelist (Policy side-effects).

        No-op when Policy is not registered (e.g. unit-test engines that only
        register ContractManagement).
        """
        if policy is None:
            return
        policy.block_account_internal(engine, hash)
        policy.clean_whitelist(engine, contract)

    def initialize(self, engine: Any, hardfork: Any | None = None) -> None:
        """Initialize contract management on genesis.

        Mirrors C# ``ContractManagement.InitializeAsync`` (ContractManagement.cs:53):
        the minimum-deployment-fee and next-available-id keys are only seeded at
        the contract's ``ActiveIn`` (genesis, ``hardfork is None``).
        """
        if hardfork is not None:
            return

        fee_key = self._create_storage_key(PREFIX_MINIMUM_DEPLOYMENT_FEE)
        fee_item = StorageItem()
        fee_item.set(DEFAULT_MINIMUM_DEPLOYMENT_FEE)
        engine.snapshot.add(fee_key, fee_item)

        id_key = self._create_storage_key(PREFIX_NEXT_AVAILABLE_ID)
        id_item = StorageItem()
        id_item.set(1)
        engine.snapshot.add(id_key, id_item)

    def on_persist(self, engine: Any) -> None:
        """Initialize natives at their activation blocks during persistence.

        Mirrors C# ``ContractManagement.OnPersistAsync`` (ContractManagement.cs:71):
        for every registered native contract, when the persisting block is an
        initialize block (genesis for genesis-active natives, or a hardfork
        activation height), create/update its contract-state record and dispatch
        ``initialize(engine, hardfork)`` for each activating hardfork.  Genesis
        seeding is performed via the ``hardfork is None`` branch.
        """
        settings = getattr(engine, "protocol_settings", None)
        block = getattr(engine, "persisting_block", None)
        if block is None and engine.snapshot is not None:
            block = getattr(engine.snapshot, "persisting_block", None)
        if settings is None or block is None:
            return
        index = int(getattr(block, "index", 0))

        for contract in sorted(
            NativeContract._contracts_by_id.values(),
            key=lambda c: c.id,
            reverse=True,
        ):
            hfs = contract.is_initialize_block(settings, index)
            if hfs is None:
                continue

            self._record_native_contract_state(engine, contract, index)

            # Genesis-active contracts are initialized on the None branch the
            # first time their record is created (mirrors C# ContractManagement
            # which only calls InitializeAsync(engine, null) when ActiveIn is
            # null and the state did not previously exist).
            if contract.contract_active_in() is None and index == 0:
                contract.initialize(engine, None)

            for hf in hfs:
                contract.initialize(engine, hf)

    def _record_native_contract_state(
        self, engine: Any, contract: NativeContract, index: int
    ) -> None:
        """Create or update the on-chain ContractState record for a native."""
        snapshot = engine.snapshot
        if snapshot is None:
            return

        contract_state = contract.get_contract_state(engine)
        key = self._create_storage_key(PREFIX_CONTRACT, contract.hash.data)

        existing = snapshot.get(key)
        if existing is None:
            snapshot.add(key, StorageItem(contract_state.to_bytes()))
            hash_key = self._create_storage_key(
                PREFIX_CONTRACT_HASH, contract.id.to_bytes(4, "big", signed=True)
            )
            snapshot.add(hash_key, StorageItem(contract.hash.data))
            event = "Deploy"
        else:
            old = ContractState.from_bytes(existing.value)
            old.update_counter += 1
            old.nef = contract_state.nef
            old.manifest = contract_state.manifest
            existing.value = old.to_bytes()
            event = "Update"

        if hasattr(engine, "send_notification"):
            engine.send_notification(self.hash, event, [contract.hash])
