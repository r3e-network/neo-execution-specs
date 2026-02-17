"""Native contract base class."""

from __future__ import annotations

import collections.abc
import dataclasses
import inspect
import json
import types
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntFlag
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin

from neo.crypto import hash160
from neo.types import UInt160

if TYPE_CHECKING:
    pass

class CallFlags(IntFlag):
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
    parameters: list[str] = field(default_factory=list)
    return_type: str = "Void"
    safe: bool = False

@dataclass
class ContractEventParameter:
    """Descriptor for an event parameter."""

    name: str
    type: str

@dataclass
class ContractEventDescriptor:
    """Descriptor for a contract event."""

    name: str
    parameters: list[ContractEventParameter] = field(default_factory=list)

@dataclass
class ContractMethodMetadata:
    """Metadata for a native contract method."""

    name: str
    handler: Callable
    cpu_fee: int = 0
    storage_fee: int = 0
    required_call_flags: CallFlags = CallFlags.NONE
    active_in: Any = None
    deprecated_in: Any = None
    manifest_parameter_names: list[str] | None = None
    descriptor: ContractMethodDescriptor = field(default_factory=ContractMethodDescriptor)
    
    def __post_init__(self):
        """Set descriptor name if not set."""
        if not self.descriptor.name:
            self.descriptor.name = self.name

@dataclass
class ContractEventMetadata:
    """Metadata for a native contract event."""

    name: str
    descriptor: ContractEventDescriptor
    order: int = 0
    active_in: Any = None
    deprecated_in: Any = None

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
    
    _contracts: dict[UInt160, NativeContract] = {}
    _contracts_by_id: dict[int, NativeContract] = {}
    _contracts_by_name: dict[str, NativeContract] = {}
    _id_counter: int = 0
    _CALLNATIVE_PUSH_SIZE: int = 1
    _CALLNATIVE_SYSCALL_SIZE: int = 5
    _CALLNATIVE_RET_SIZE: int = 1
    _CALLNATIVE_STUB_SIZE: int = (
        _CALLNATIVE_PUSH_SIZE + _CALLNATIVE_SYSCALL_SIZE + _CALLNATIVE_RET_SIZE
    )
    _CALLNATIVE_SYSCALL_OFFSET: int = _CALLNATIVE_PUSH_SIZE
    
    def __init__(self) -> None:
        self._id = self._get_next_id()
        self._hash = self._calculate_hash()
        self._methods: dict[str, ContractMethodMetadata] = {}
        self._methods_by_name: dict[str, list[ContractMethodMetadata]] = {}
        self._method_entries: list[ContractMethodMetadata] = []
        self._ordered_method_entries: list[ContractMethodMetadata] = []
        self._methods_by_offset: dict[int, ContractMethodMetadata] = {}
        self._method_order: list[str] = []
        self._next_method_offset: int = 0
        self._events: list[ContractEventMetadata] = []
        self._next_event_order: int = 0
        self._register_methods()
        self._register_events()
        self._finalize_method_order()

        # Register contract
        NativeContract._contracts[self._hash] = self
        NativeContract._contracts_by_id[self._id] = self
        NativeContract._contracts_by_name[self.name] = self
    
    @classmethod
    def _get_next_id(cls) -> int:
        NativeContract._id_counter -= 1
        return NativeContract._id_counter
    
    def _calculate_hash(self) -> UInt160:
        """Calculate contract hash using ScriptBuilder (matches C# Helper.GetContractHash).

        The C# reference builds a small script:
            ABORT + PUSH(sender) + PUSH(nefCheckSum) + PUSH(name)
        then hashes it with Hash160.  For native contracts sender is
        UInt160.Zero and nefCheckSum is 0.
        """
        from neo.vm.opcode import OpCode
        from neo.vm.script_builder import ScriptBuilder

        sb = ScriptBuilder()
        sb.emit(OpCode.ABORT)
        sb.emit_push(b'\x00' * 20)   # sender = UInt160.Zero
        sb.emit_push(0)               # nefCheckSum = 0 for native
        sb.emit_push(self.name)       # contract name as string
        return UInt160(hash160(sb.to_array()))
    
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

    def _contract_activations(self) -> tuple[Any | None, ...]:
        """Hardfork activations for contract deployment/availability.

        Mirrors Neo's ``Activations`` list semantics where the first
        activation controls when the contract becomes active.
        """
        return (None,)

    def contract_active_in(self) -> Any | None:
        """Return the hardfork that activates this contract, if any."""
        activations = self._contract_activations()
        return activations[0] if activations else None

    def is_contract_active(self, context: Any) -> bool:
        """Whether this native contract is active in *context*."""
        activation = self.contract_active_in()
        if activation is None:
            return True
        return self.is_hardfork_enabled(context, activation)

    @staticmethod
    def _hardfork_height(settings: Any, hardfork: Any) -> int | None:
        hardforks = getattr(settings, "hardforks", None)
        if isinstance(hardforks, dict):
            height = hardforks.get(hardfork)
            if height is not None:
                return int(height)
        return None

    @classmethod
    def _context_block_index(cls, context: Any) -> int:
        _, snapshot = cls._hardfork_context(context)
        block = getattr(snapshot, "persisting_block", None) if snapshot is not None else None
        if block is None:
            block = getattr(context, "persisting_block", None)
        if block is None:
            return 0
        return int(getattr(block, "index", 0))

    def _used_hardforks(self) -> set[Any]:
        used: set[Any] = set()
        for activation in self._contract_activations():
            if activation is not None:
                used.add(activation)
        for method in self._method_entries:
            if method.active_in is not None:
                used.add(method.active_in)
            if method.deprecated_in is not None:
                used.add(method.deprecated_in)
        for event in self._events:
            if event.active_in is not None:
                used.add(event.active_in)
            if event.deprecated_in is not None:
                used.add(event.deprecated_in)
        return used

    def _native_update_counter(self, context: Any) -> int:
        settings, _ = self._hardfork_context(context)
        if settings is None:
            return 0

        index = self._context_block_index(context)
        active_in = self.contract_active_in()
        if active_in is None:
            creation_height = 0
        else:
            active_height = self._hardfork_height(settings, active_in)
            if active_height is None or active_height > index:
                return 0
            creation_height = active_height

        init_heights: set[int] = {creation_height}
        for hardfork in self._used_hardforks():
            height = self._hardfork_height(settings, hardfork)
            if height is None:
                continue
            if height < creation_height or height > index:
                continue
            init_heights.add(height)
        return max(0, len(init_heights) - 1)
    
    def _register_methods(self) -> None:
        """Register contract methods. Override in subclasses."""
        pass

    def _register_events(self) -> None:
        """Register contract events. Override in subclasses."""
        pass
    
    def _register_method(
        self,
        name: str,
        handler: Callable,
        cpu_fee: int = 0,
        storage_fee: int = 0,
        call_flags: CallFlags = CallFlags.NONE,
        active_in: Any = None,
        deprecated_in: Any = None,
        manifest_parameter_names: list[str] | None = None,
    ) -> None:
        """Register a contract method.

        Each method is assigned a sequential descriptor offset matching
        Neo native-script stub layout:

            PUSH0 (version) + SYSCALL CallNative + RET

        So descriptor offsets advance by 7 bytes (1 + 5 + 1). CallNative
        dispatch itself resolves at the SYSCALL instruction pointer
        (descriptor offset + 1) via ``get_active_methods_by_offset``.

        Note: Neo core builds native scripts dynamically from active
        methods at runtime; this registry is a simplified local model.
        """
        offset = self._next_method_offset
        self._next_method_offset += self._CALLNATIVE_STUB_SIZE

        descriptor = ContractMethodDescriptor(
            name=name,
            offset=offset,
            safe=bool((call_flags & ~CallFlags.READ_ONLY) == 0),
        )
        metadata = ContractMethodMetadata(
            name=name,
            handler=handler,
            cpu_fee=cpu_fee,
            storage_fee=storage_fee,
            required_call_flags=call_flags,
            active_in=active_in,
            deprecated_in=deprecated_in,
            manifest_parameter_names=manifest_parameter_names,
            descriptor=descriptor,
        )
        self._methods[name] = metadata
        self._methods_by_name.setdefault(name, []).append(metadata)
        self._method_entries.append(metadata)
        self._methods_by_offset[offset] = metadata
        self._method_order.append(name)

    def _register_event(
        self,
        name: str,
        parameters: list[tuple[str, str]],
        *,
        order: int | None = None,
        active_in: Any = None,
        deprecated_in: Any = None,
    ) -> None:
        """Register a contract event descriptor."""
        event_order = self._next_event_order if order is None else int(order)
        if event_order >= self._next_event_order:
            self._next_event_order = event_order + 1

        descriptor = ContractEventDescriptor(
            name=name,
            parameters=[
                ContractEventParameter(name=param_name, type=param_type)
                for param_name, param_type in parameters
            ],
        )
        metadata = ContractEventMetadata(
            name=name,
            descriptor=descriptor,
            order=event_order,
            active_in=active_in,
            deprecated_in=deprecated_in,
        )
        self._events.append(metadata)

    @staticmethod
    def _method_parameter_count(method: ContractMethodMetadata) -> int:
        """Get ABI parameter count excluding context (engine/snapshot)."""
        signature = inspect.signature(method.handler)
        parameters = list(signature.parameters.values())
        count = 0
        for index, parameter in enumerate(parameters):
            if index == 0 and parameter.name in {"engine", "snapshot", "context"}:
                continue
            if NativeContract._is_compat_context_parameter(parameters, index, parameter):
                continue
            count += 1
        return count

    def _finalize_method_order(self) -> None:
        """Apply Neo native-method canonical ordering and descriptor offsets."""
        ordered = sorted(
            self._method_entries,
            key=lambda method: (method.name, self._method_parameter_count(method)),
        )
        self._ordered_method_entries = ordered
        self._method_order = [method.name for method in ordered]
        self._methods_by_offset = {}
        for index, method in enumerate(ordered):
            offset = index * self._CALLNATIVE_STUB_SIZE
            method.descriptor.offset = offset
            self._methods_by_offset[offset] = method
    
    def _create_storage_key(self, prefix: int, *args) -> StorageKey:
        """Create a storage key for this contract."""
        return StorageKey.create(self._id, prefix, *args)

    def _get_active_method_entries(
        self,
        context: Any,
    ) -> list[tuple[int, int, ContractMethodMetadata]]:
        """Return active methods with descriptor + SYSCALL offsets."""
        entries: list[tuple[int, int, ContractMethodMetadata]] = []
        descriptor_offset = 0
        for method in self._ordered_method_entries:
            if not self._is_method_active(context, method):
                continue
            syscall_offset = descriptor_offset + self._CALLNATIVE_SYSCALL_OFFSET
            entries.append((descriptor_offset, syscall_offset, method))
            descriptor_offset += self._CALLNATIVE_STUB_SIZE
        return entries

    def get_method_by_offset(self, offset: int) -> ContractMethodMetadata | None:
        """Look up a registered method by its script offset.

        This offset corresponds to the method descriptor offset (the
        start of the native stub, before PUSH0).
        """
        return self._methods_by_offset.get(offset)

    def get_method_if_active(
        self,
        name: str,
        context: Any,
    ) -> ContractMethodMetadata | None:
        """Look up a method by name and ensure it is active in *context*."""
        variants = self._methods_by_name.get(name)
        if not variants:
            return None
        for method in reversed(variants):
            if self._is_method_active(context, method):
                return method
        return None

    def _is_method_active(self, context: Any, method: ContractMethodMetadata) -> bool:
        """Check whether a method is active in the given hardfork context."""
        if method.active_in is not None and not self.is_hardfork_enabled(context, method.active_in):
            return False
        if method.deprecated_in is not None and self.is_hardfork_enabled(context, method.deprecated_in):
            return False
        return True

    def get_active_methods_by_offset(self, context: Any) -> dict[int, ContractMethodMetadata]:
        """Build the callnative offset map for methods active in *context*."""
        return {
            syscall_offset: method
            for _, syscall_offset, method in self._get_active_method_entries(context)
        }

    def get_method_by_callnative_offset(
        self,
        context: Any,
        instruction_pointer: int,
    ) -> ContractMethodMetadata | None:
        """Resolve a callnative method by SYSCALL instruction pointer."""
        if instruction_pointer < 0:
            return None
        return self.get_active_methods_by_offset(context).get(instruction_pointer)

    def get_method(self, name: str) -> ContractMethodMetadata | None:
        """Look up a registered method by name."""
        variants = self._methods_by_name.get(name)
        if not variants:
            return None
        return variants[-1]

    @staticmethod
    def _is_context_parameter(parameter: inspect.Parameter) -> bool:
        return parameter.name in {"engine", "snapshot", "context"}

    @staticmethod
    def _is_compat_context_parameter(
        parameters: list[inspect.Parameter],
        index: int,
        parameter: inspect.Parameter,
    ) -> bool:
        """Detect internal ``(value, context=None)`` compatibility signatures."""
        return (
            len(parameters) == 2
            and index == 1
            and parameter.name == "context"
            and parameter.default is not inspect._empty
        )

    @classmethod
    def _normalize_manifest_annotation(cls, annotation: Any) -> str:
        """Convert a Python type annotation into a Neo manifest ABI type."""
        if annotation is inspect._empty or annotation is Any:
            return "Any"
        if annotation is None or annotation is type(None):
            return "Void"

        if isinstance(annotation, str):
            value = annotation.strip().lower()
            if value in {"none", "void"}:
                return "Void"
            if "uint160" in value:
                return "Hash160"
            if "uint256" in value:
                return "Hash256"
            if "bool" in value:
                return "Boolean"
            if "int" in value:
                return "Integer"
            if value in {"bytes", "bytearray"}:
                return "ByteArray"
            if "str" in value:
                return "String"
            if "list" in value or "tuple" in value or "set" in value:
                return "Array"
            if "dict" in value or "map" in value:
                return "Map"
            if "iterator" in value or "iterable" in value:
                return "InteropInterface"
            return "Any"

        origin = get_origin(annotation)
        if origin in (list, tuple, set, frozenset):
            return "Array"
        if origin is dict:
            return "Map"
        if origin in (
            collections.abc.Iterator,
            collections.abc.Iterable,
            collections.abc.Generator,
        ):
            return "InteropInterface"
        if origin in (types.UnionType, Union):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) == 1:
                return cls._normalize_manifest_annotation(args[0])
            return "Any"

        if annotation is bool:
            return "Boolean"
        if annotation is int:
            return "Integer"
        if annotation in (bytes, bytearray):
            return "ByteArray"
        if annotation is str:
            return "String"
        if annotation in (list, tuple, set, frozenset):
            return "Array"
        if annotation is dict:
            return "Map"
        if annotation is object:
            return "Any"

        name = getattr(annotation, "__name__", "")
        if name == "UInt160":
            return "Hash160"
        if name == "UInt256":
            return "Hash256"
        if name == "ECPoint":
            return "PublicKey"
        if isinstance(annotation, type):
            from enum import Enum

            if issubclass(annotation, Enum):
                return "Integer"
            if dataclasses.is_dataclass(annotation):
                return "Array"
            return "InteropInterface"

        return "Any"

    def _build_manifest_method(
        self,
        descriptor_offset: int,
        method: ContractMethodMetadata,
    ) -> dict[str, Any]:
        signature = inspect.signature(method.handler)
        parameters_spec = list(signature.parameters.values())
        try:
            from typing import get_type_hints

            type_hints = get_type_hints(method.handler)
        except Exception:
            type_hints = {}

        parameters: list[dict[str, str]] = []
        manifest_parameter_names = method.manifest_parameter_names
        manifest_index = 0
        for index, parameter in enumerate(parameters_spec):
            if index == 0 and self._is_context_parameter(parameter):
                continue
            if self._is_compat_context_parameter(parameters_spec, index, parameter):
                continue
            annotation = type_hints.get(parameter.name, parameter.annotation)
            parameter_name = parameter.name
            if (
                manifest_parameter_names is not None
                and manifest_index < len(manifest_parameter_names)
            ):
                parameter_name = manifest_parameter_names[manifest_index]
            parameters.append(
                {
                    "name": parameter_name,
                    "type": self._normalize_manifest_annotation(annotation),
                }
            )
            manifest_index += 1

        return_annotation = type_hints.get("return", signature.return_annotation)
        return {
            "name": method.name,
            "parameters": parameters,
            "returntype": self._normalize_manifest_annotation(return_annotation),
            "offset": descriptor_offset,
            "safe": bool(method.descriptor.safe),
        }

    def _is_event_active(self, context: Any, event: ContractEventMetadata) -> bool:
        if event.active_in is not None and not self.is_hardfork_enabled(context, event.active_in):
            return False
        if event.deprecated_in is not None and self.is_hardfork_enabled(context, event.deprecated_in):
            return False
        return True

    def _build_manifest_event(self, event: ContractEventMetadata) -> dict[str, Any]:
        return {
            "name": event.name,
            "parameters": [
                {"name": parameter.name, "type": parameter.type}
                for parameter in event.descriptor.parameters
            ],
        }

    def _active_manifest_events(self, context: Any) -> list[dict[str, Any]]:
        active = [event for event in self._events if self._is_event_active(context, event)]
        active.sort(key=lambda event: event.order)
        return [self._build_manifest_event(event) for event in active]

    def _native_supported_standards(self, context: Any) -> list[str]:
        """Override in subclasses that expose supported standards."""
        return []

    def _compose_native_manifest(self, context: Any, manifest: dict[str, Any]) -> None:
        """Hook for native contracts to customize generated manifests."""
        return

    @staticmethod
    def _native_stub() -> bytes:
        """Build one callnative stub: PUSH0 + SYSCALL CallNative + RET."""
        from neo.smartcontract.interop_service import get_interop_hash
        from neo.vm.opcode import OpCode

        syscall = get_interop_hash("System.Contract.CallNative")
        return (
            bytes((int(OpCode.PUSH0), int(OpCode.SYSCALL)))
            + syscall.to_bytes(4, "little")
            + bytes((int(OpCode.RET),))
        )

    def get_contract_state(self, context: Any, hash: UInt160 | None = None) -> Any:
        """Generate the active native ``ContractState`` for this context.

        The optional ``hash`` parameter exists for ``ContractManagement``
        compatibility helpers; non-management native contracts ignore it.
        """
        from neo.native.contract_management import ContractState

        active = self._get_active_method_entries(context)
        methods = [
            self._build_manifest_method(descriptor_offset, method)
            for descriptor_offset, _, method in active
        ]
        manifest = {
            "name": self.name,
            "groups": [],
            "features": {},
            "supportedstandards": self._native_supported_standards(context),
            "abi": {
                "methods": methods,
                "events": self._active_manifest_events(context),
            },
            "permissions": [{"contract": "*", "methods": "*"}],
            "trusts": "*",
            "extra": None,
        }
        self._compose_native_manifest(context, manifest)

        script = self._native_stub() * len(active)
        manifest_bytes = json.dumps(manifest, separators=(",", ":")).encode("utf-8")
        return ContractState(
            id=self.id,
            update_counter=self._native_update_counter(context),
            hash=self.hash,
            nef=script,
            manifest=manifest_bytes,
        )

    @staticmethod
    def _hardfork_context(context: Any) -> tuple[Any, Any]:
        """Extract protocol settings + snapshot from an engine/snapshot-like object."""
        settings = getattr(context, "protocol_settings", None)
        snapshot = getattr(context, "snapshot", None)
        if snapshot is None and hasattr(context, "persisting_block"):
            snapshot = context
        if settings is None and snapshot is not None:
            settings = getattr(snapshot, "protocol_settings", None)
        return settings, snapshot

    @classmethod
    def is_hardfork_enabled(cls, context: Any, hardfork: Any) -> bool:
        """Check hardfork activation from either engine or snapshot context.

        If no protocol settings are available, this returns True to preserve
        backwards compatibility with lightweight unit-test stubs.
        """
        settings, snapshot = cls._hardfork_context(context)
        if settings is None:
            return True

        block = getattr(snapshot, "persisting_block", None) if snapshot is not None else None
        if block is None:
            checker = getattr(settings, "is_hardfork_enabled", None)
            if callable(checker):
                return bool(checker(hardfork, 0))
            hardforks = getattr(settings, "hardforks", {})
            height = hardforks.get(hardfork)
            if height is None:
                return False
            return int(height) <= 0

        checker = getattr(settings, "is_hardfork_enabled", None)
        if not callable(checker):
            return False
        index = int(getattr(block, "index", 0))
        return bool(checker(hardfork, index))

    @classmethod
    def require_hardfork(cls, context: Any, hardfork: Any, method_name: str) -> None:
        """Raise when a hardfork-gated method is not active."""
        if not cls.is_hardfork_enabled(context, hardfork):
            raise KeyError(f"Method not active for hardfork: {method_name}")
    
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
    def get_contract(cls, hash: UInt160) -> NativeContract | None:
        """Get a native contract by hash."""
        return cls._contracts.get(hash)
    
    @classmethod
    def get_contract_by_id(cls, id: int) -> NativeContract | None:
        """Get a native contract by ID."""
        return cls._contracts_by_id.get(id)
    
    @classmethod
    def get_contract_by_name(cls, name: str) -> NativeContract | None:
        """Get a native contract by name."""
        return cls._contracts_by_name.get(name)

    @classmethod
    def is_native(cls, hash: UInt160) -> bool:
        """Check if a hash is a native contract."""
        return hash in cls._contracts
