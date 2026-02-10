"""Native contract base class."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from neo.types import UInt160
from neo.crypto import hash160

if TYPE_CHECKING:
    pass


class CallFlags(IntEnum):
    """Call flags for contract methods."""
    NONE = 0
    READ_STATES = 0b00000001
    WRITE_STATES = 0b00000010
    ALLOW_CALL = 0b00000100
    ALLOW_NOTIFY = 0b00001000
    STATES = READ_STATES | WRITE_STATES
    READ_ONLY = READ_STATES | ALLOW_CALL
    ALL = STATES | ALLOW_CALL | ALLOW_NOTIFY


@dataclass
class ContractMethodDescriptor:
    """Descriptor for a contract method."""
    name: str = ""
    offset: int = 0
    parameters: List[str] = field(default_factory=list)
    return_type: str = "Void"
    safe: bool = False


@dataclass
class ContractMethodMetadata:
    """Metadata for a native contract method."""
    name: str
    handler: Callable
    cpu_fee: int = 0
    storage_fee: int = 0
    required_call_flags: CallFlags = CallFlags.NONE
    descriptor: ContractMethodDescriptor = field(default_factory=ContractMethodDescriptor)
    
    def __post_init__(self):
        """Set descriptor name if not set."""
        if not self.descriptor.name:
            self.descriptor.name = self.name


class StorageKey:
    """Storage key for native contracts."""
    
    def __init__(self, contract_id: int, key: bytes) -> None:
        self.id = contract_id
        self.key = key
    
    @classmethod
    def create(cls, contract_id: int, prefix: int, *args) -> StorageKey:
        """Create a storage key with prefix and optional data."""
        key_data = bytes([prefix])
        for arg in args:
            if isinstance(arg, int):
                key_data += arg.to_bytes(4, 'little')
            elif isinstance(arg, bytes):
                key_data += arg
            elif isinstance(arg, UInt160):
                key_data += arg.data
        return cls(contract_id, key_data)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, StorageKey):
            return self.id == other.id and self.key == other.key
        return False
    
    def __hash__(self) -> int:
        return hash((self.id, self.key))


class StorageItem:
    """Storage item for native contracts."""
    
    def __init__(self, value: bytes = b"") -> None:
        self._value = value
    
    @property
    def value(self) -> bytes:
        return self._value
    
    @value.setter
    def value(self, val: bytes) -> None:
        self._value = val
    
    def set(self, value: Any) -> None:
        """Set the value."""
        if isinstance(value, int):
            self._value = value.to_bytes((value.bit_length() + 8) // 8, 'little', signed=True) if value else b'\x00'
        elif isinstance(value, bytes):
            self._value = value
        else:
            self._value = bytes(value)
    
    def add(self, value: int) -> None:
        """Add to the current integer value."""
        current = int.from_bytes(self._value, 'little', signed=True) if self._value else 0
        self.set(current + value)
    
    def __int__(self) -> int:
        if not self._value:
            return 0
        return int.from_bytes(self._value, 'little', signed=True)


class NativeContract(ABC):
    """Base class for native contracts."""
    
    _contracts: Dict[UInt160, 'NativeContract'] = {}
    _contracts_by_id: Dict[int, 'NativeContract'] = {}
    _contracts_by_name: Dict[str, 'NativeContract'] = {}
    _id_counter: int = 0
    
    def __init__(self) -> None:
        self._id = self._get_next_id()
        self._hash = self._calculate_hash()
        self._methods: Dict[str, ContractMethodMetadata] = {}
        self._methods_by_offset: Dict[int, ContractMethodMetadata] = {}
        self._next_method_offset: int = 0
        self._register_methods()

        # Register contract
        NativeContract._contracts[self._hash] = self
        NativeContract._contracts_by_id[self._id] = self
        NativeContract._contracts_by_name[self.name] = self
    
    @classmethod
    def _get_next_id(cls) -> int:
        NativeContract._id_counter -= 1
        return NativeContract._id_counter
    
    def _calculate_hash(self) -> UInt160:
        """Calculate contract hash: Hash160(0x00 * 20 + nef_checksum + name)."""
        # For native contracts: Hash160(sender + nef_checksum + name)
        # sender = UInt160.Zero, nef_checksum = 0
        sender = b'\x00' * 20
        nef_checksum = (0).to_bytes(4, 'little')
        name_bytes = self.name.encode('utf-8')
        
        # Build the data to hash
        data = sender + nef_checksum + bytes([len(name_bytes)]) + name_bytes
        return UInt160(hash160(data))
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Contract name."""
        ...
    
    @property
    def id(self) -> int:
        """Contract ID."""
        return self._id
    
    @property
    def hash(self) -> UInt160:
        """Contract script hash."""
        return self._hash
    
    def _register_methods(self) -> None:
        """Register contract methods. Override in subclasses."""
        pass
    
    def _register_method(
        self,
        name: str,
        handler: Callable,
        cpu_fee: int = 0,
        storage_fee: int = 0,
        call_flags: CallFlags = CallFlags.NONE
    ) -> None:
        """Register a contract method.

        Each method is assigned a sequential offset (multiples of 5,
        matching the C# reference where each native stub is 5 bytes:
        ``PUSH<version> + SYSCALL CallNative``).  The offset is stored
        in the method descriptor and in ``_methods_by_offset`` for
        reverse lookup during ``System.Contract.CallNative`` dispatch.
        """
        offset = self._next_method_offset
        self._next_method_offset += 5

        descriptor = ContractMethodDescriptor(name=name, offset=offset)
        metadata = ContractMethodMetadata(
            name=name,
            handler=handler,
            cpu_fee=cpu_fee,
            storage_fee=storage_fee,
            required_call_flags=call_flags,
            descriptor=descriptor,
        )
        self._methods[name] = metadata
        self._methods_by_offset[offset] = metadata
    
    def _create_storage_key(self, prefix: int, *args) -> StorageKey:
        """Create a storage key for this contract."""
        return StorageKey.create(self._id, prefix, *args)

    def get_method_by_offset(self, offset: int) -> Optional[ContractMethodMetadata]:
        """Look up a registered method by its script offset.

        Used by ``System.Contract.CallNative`` to resolve which method
        the native contract stub is invoking.
        """
        return self._methods_by_offset.get(offset)

    def get_method(self, name: str) -> Optional[ContractMethodMetadata]:
        """Look up a registered method by name."""
        return self._methods.get(name)
    
    def initialize(self, engine: Any) -> None:
        """Initialize the contract. Called on genesis block."""
        pass
    
    def on_persist(self, engine: Any) -> None:
        """Called when a block is being persisted."""
        pass
    
    def post_persist(self, engine: Any) -> None:
        """Called after a block is persisted."""
        pass
    
    @classmethod
    def get_contract(cls, hash: UInt160) -> Optional['NativeContract']:
        """Get a native contract by hash."""
        return cls._contracts.get(hash)
    
    @classmethod
    def get_contract_by_id(cls, id: int) -> Optional['NativeContract']:
        """Get a native contract by ID."""
        return cls._contracts_by_id.get(id)
    
    @classmethod
    def get_contract_by_name(cls, name: str) -> Optional['NativeContract']:
        """Get a native contract by name."""
        return cls._contracts_by_name.get(name)

    @classmethod
    def is_native(cls, hash: UInt160) -> bool:
        """Check if a hash is a native contract."""
        return hash in cls._contracts
