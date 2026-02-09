"""Contract Management native contract."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from neo.types import UInt160
from neo.native.native_contract import NativeContract, CallFlags, StorageItem
from neo.crypto import hash160


# Storage prefixes
PREFIX_MINIMUM_DEPLOYMENT_FEE = 20
PREFIX_NEXT_AVAILABLE_ID = 15
PREFIX_CONTRACT = 8
PREFIX_CONTRACT_HASH = 12

# Default minimum deployment fee (10 GAS)
DEFAULT_MINIMUM_DEPLOYMENT_FEE = 10_00000000


@dataclass
class ContractState:
    """State of a deployed contract."""
    id: int = 0
    update_counter: int = 0
    hash: Optional[UInt160] = None
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
    def from_bytes(cls, data: bytes) -> 'ContractState':
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
    
    def __init__(self) -> None:
        super().__init__()
    
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
        self._register_method("getContract", self.get_contract,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("getContractById", self.get_contract_by_id,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("hasMethod", self.has_method,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("deploy", self.deploy,
                            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY)
        self._register_method("update", self.update,
                            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY)
        self._register_method("destroy", self.destroy,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY)
    
    def get_minimum_deployment_fee(self, snapshot: Any) -> int:
        """Get minimum deployment fee."""
        key = self._create_storage_key(PREFIX_MINIMUM_DEPLOYMENT_FEE)
        item = snapshot.get(key)
        return int(item) if item else DEFAULT_MINIMUM_DEPLOYMENT_FEE
    
    def set_minimum_deployment_fee(self, engine: Any, value: int) -> None:
        """Set minimum deployment fee. Committee only."""
        if value < 0:
            raise ValueError("Value cannot be negative")
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
    
    def get_contract(self, snapshot: Any, hash: UInt160) -> Optional[ContractState]:
        """Get a deployed contract by hash."""
        key = self._create_storage_key(PREFIX_CONTRACT, hash.data)
        item = snapshot.get(key)
        if item is None:
            return None
        return ContractState.from_bytes(item.value)
    
    def get_contract_by_id(self, snapshot: Any, id: int) -> Optional[ContractState]:
        """Get a deployed contract by ID."""
        key = self._create_storage_key(PREFIX_CONTRACT_HASH, id)
        item = snapshot.get(key)
        if item is None:
            return None
        hash = UInt160(item.value)
        return self.get_contract(snapshot, hash)
    
    def has_method(self, snapshot: Any, hash: UInt160, method: str, pcount: int) -> bool:
        """Check if a contract has a specific method.

        Parses the contract's manifest JSON and inspects the ABI to
        verify that a method with the given *name* and *parameter count*
        actually exists.
        """
        import json as _json

        contract = self.get_contract(snapshot, hash)
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
    
    def deploy(self, engine: Any, nef_file: bytes, manifest: bytes, 
               data: Any = None) -> ContractState:
        """Deploy a new contract."""
        if not nef_file:
            raise ValueError("NEF file cannot be empty")
        if not manifest:
            raise ValueError("Manifest cannot be empty")
        
        # Calculate deployment fee
        storage_price = engine.storage_price
        min_fee = self.get_minimum_deployment_fee(engine.snapshot)
        fee = max(storage_price * (len(nef_file) + len(manifest)), min_fee)
        engine.add_fee(fee)
        
        # Calculate contract hash
        tx = engine.script_container
        contract_hash = self._calculate_contract_hash(tx.sender, nef_file, manifest)
        
        # Check if contract already exists
        key = self._create_storage_key(PREFIX_CONTRACT, contract_hash.data)
        if engine.snapshot.contains(key):
            raise ValueError(f"Contract already exists: {contract_hash}")
        
        # Create contract state
        contract = ContractState(
            id=self._get_next_available_id(engine.snapshot),
            update_counter=0,
            hash=contract_hash,
            nef=nef_file,
            manifest=manifest
        )
        
        # Store contract
        engine.snapshot.add(key, StorageItem(contract.to_bytes()))
        hash_key = self._create_storage_key(PREFIX_CONTRACT_HASH, contract.id)
        engine.snapshot.add(hash_key, StorageItem(contract_hash.data))
        
        # Send notification
        engine.send_notification(self.hash, "Deploy", [contract_hash])
        
        return contract
    
    def _calculate_contract_hash(self, sender: UInt160, nef: bytes, 
                                  manifest: bytes) -> UInt160:
        """Calculate contract hash from sender, NEF checksum, and name."""
        import json
        # Parse manifest to get name
        manifest_obj = json.loads(manifest.decode('utf-8'))
        name = manifest_obj.get('name', '')
        
        # NEF checksum is the last 4 bytes of the serialized NEF
        import struct
        if len(nef) >= 4:
            nef_checksum = struct.unpack_from('<I', nef, len(nef) - 4)[0]
        else:
            nef_checksum = 0
        
        # Build hash input
        data = sender.data
        data += nef_checksum.to_bytes(4, 'little')
        data += bytes([len(name)]) + name.encode('utf-8')
        
        return UInt160(hash160(data))
    
    def update(self, engine: Any, nef_file: Optional[bytes], 
               manifest: Optional[bytes], data: Any = None) -> None:
        """Update an existing contract."""
        if nef_file is None and manifest is None:
            raise ValueError("NEF and manifest cannot both be null")
        
        # Get calling contract
        calling_hash = engine.calling_script_hash
        key = self._create_storage_key(PREFIX_CONTRACT, calling_hash.data)
        item = engine.snapshot.get_and_change(key)
        if item is None:
            raise ValueError(f"Contract does not exist: {calling_hash}")
        
        contract = ContractState.from_bytes(item.value)
        
        # Update NEF if provided
        if nef_file is not None:
            if not nef_file:
                raise ValueError("NEF file cannot be empty")
            contract.nef = nef_file
        
        # Update manifest if provided
        if manifest is not None:
            if not manifest:
                raise ValueError("Manifest cannot be empty")
            contract.manifest = manifest
        
        contract.update_counter += 1
        item.value = contract.to_bytes()
        
        engine.send_notification(self.hash, "Update", [calling_hash])
    
    def destroy(self, engine: Any) -> None:
        """Destroy the calling contract."""
        calling_hash = engine.calling_script_hash
        key = self._create_storage_key(PREFIX_CONTRACT, calling_hash.data)
        item = engine.snapshot.get(key)
        if item is None:
            return
        
        contract = ContractState.from_bytes(item.value)
        
        # Delete contract
        engine.snapshot.delete(key)
        hash_key = self._create_storage_key(PREFIX_CONTRACT_HASH, contract.id)
        engine.snapshot.delete(hash_key)
        
        # Delete contract storage
        engine.snapshot.delete_contract_storage(contract.id)
        
        engine.send_notification(self.hash, "Destroy", [calling_hash])
    
    def initialize(self, engine: Any) -> None:
        """Initialize contract management on genesis."""
        fee_key = self._create_storage_key(PREFIX_MINIMUM_DEPLOYMENT_FEE)
        fee_item = StorageItem()
        fee_item.set(DEFAULT_MINIMUM_DEPLOYMENT_FEE)
        engine.snapshot.add(fee_key, fee_item)
        
        id_key = self._create_storage_key(PREFIX_NEXT_AVAILABLE_ID)
        id_item = StorageItem()
        id_item.set(1)
        engine.snapshot.add(id_key, id_item)
