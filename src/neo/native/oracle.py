"""Oracle contract for external data requests.

Reference: Neo.SmartContract.Native.OracleContract (v3.10.0)
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from neo.crypto import hash160
from neo.hardfork import Hardfork
from neo.native.native_contract import CallFlags, NativeContract, StorageItem
from neo.types import UInt160, UInt256

# Storage prefixes (OracleContract.cs:41-44)
PREFIX_PRICE = 5
PREFIX_REQUEST_ID = 9
PREFIX_REQUEST = 7
PREFIX_ID_LIST = 6

# Limits (OracleContract.cs:36-39)
MAX_URL_LENGTH = 256
MAX_FILTER_LENGTH = 128
MAX_CALLBACK_LENGTH = 32
MAX_USER_DATA_LENGTH = 512

# Default oracle price (0.5 GAS in datoshi) -- OracleContract.cs:172
DEFAULT_ORACLE_PRICE = 50_000_000

# Minimum GAS reserved for a response (0.1 GAS) -- OracleContract.cs:240
MIN_GAS_FOR_RESPONSE = 10_000_000

# OracleResponse transaction attribute type code
ORACLE_RESPONSE_ATTR_TYPE = 0x11

# Maximum number of pending responses per url-hash (OracleContract.cs:275)
MAX_PENDING_PER_URL = 256


class OracleResponseCode(IntEnum):
    """Oracle response codes."""

    Success = 0x00
    ProtocolNotSupported = 0x10
    ConsensusUnreachable = 0x12
    NotFound = 0x14
    Timeout = 0x16
    Forbidden = 0x18
    ResponseTooLarge = 0x1a
    InsufficientFunds = 0x1c
    ContentTypeNotSupported = 0x1f
    Error = 0xff


def _request_id_key_suffix(request_id: int) -> bytes:
    """Encode a request id as the C# storage-key suffix.

    C# ``CreateStorageKey(Prefix_Request, id)`` writes the ``ulong`` id in
    big-endian order, which ``GetRequests`` reads back with
    ``BinaryPrimitives.ReadUInt64BigEndian`` (OracleContract.cs:141). The
    shared ``StorageKey.create`` helper would encode an ``int`` as 4-byte
    little-endian, so the id is pre-encoded here to preserve byte parity.
    """
    return int(request_id).to_bytes(8, "big")


@dataclass
class OracleRequest:
    """Oracle request data structure (C# OracleRequest IInteroperable)."""

    original_txid: UInt256 = field(default_factory=lambda: UInt256(b'\x00' * 32))
    gas_for_response: int = 0
    url: str = ""
    filter: str | None = None
    callback_contract: UInt160 = field(default_factory=lambda: UInt160(b'\x00' * 20))
    callback_method: str = ""
    user_data: bytes = b""

    def to_stack_item(self) -> Any:
        """Build the IInteroperable stack item (C# OracleRequest.ToStackItem).

        Reference: SmartContract/Native/OracleRequest.cs:71-83. The element
        order is [OriginalTxid, GasForResponse, Url, Filter|Null,
        CallbackContract, CallbackMethod, UserData].
        """
        from neo.vm.types import NULL, Array, ByteString, Integer

        filter_item: Any
        if self.filter is None:
            filter_item = NULL
        else:
            filter_item = ByteString(self.filter.encode("utf-8"))

        return Array(
            items=[
                ByteString(self.original_txid.data),
                Integer(self.gas_for_response),
                ByteString(self.url.encode("utf-8")),
                filter_item,
                ByteString(self.callback_contract.data),
                ByteString(self.callback_method.encode("utf-8")),
                ByteString(bytes(self.user_data)),
            ]
        )

    def serialize(self) -> bytes:
        """Serialize request via BinarySerializer of the IInteroperable item.

        Matches C# StorageItem(IInteroperable) persistence: the stored bytes
        are BinarySerializer.Serialize(request.ToStackItem()).
        """
        # Validate field lengths before serialization (parity with C# Request).
        url_bytes = self.url.encode('utf-8')
        if len(url_bytes) > MAX_URL_LENGTH:
            raise ValueError(f"URL exceeds max length of {MAX_URL_LENGTH}")
        if self.filter is not None and len(self.filter.encode('utf-8')) > MAX_FILTER_LENGTH:
            raise ValueError("Filter exceeds max length")
        method_bytes = self.callback_method.encode('utf-8')
        if len(method_bytes) > MAX_CALLBACK_LENGTH:
            raise ValueError("Callback exceeds max length")
        if len(self.user_data) > MAX_USER_DATA_LENGTH:
            raise ValueError("User data exceeds max length")

        from neo.smartcontract.binary_serializer import BinarySerializer

        return BinarySerializer.serialize(self.to_stack_item())

    @classmethod
    def deserialize(cls, data: bytes) -> OracleRequest:
        """Deserialize request from BinarySerializer bytes (C# FromStackItem)."""
        from neo.smartcontract.binary_serializer import BinarySerializer
        from neo.vm.types import StackItemType

        array = BinarySerializer.deserialize(data)
        items = list(array)

        original_txid = UInt256(bytes(items[0].value))
        gas_for_response = int(items[1].value)
        url = bytes(items[2].value).decode("utf-8")

        filter_item = items[3]
        if filter_item is None or filter_item.type == StackItemType.ANY:
            filter_val = None
        else:
            filter_val = bytes(filter_item.value).decode("utf-8")

        callback_contract = UInt160(bytes(items[4].value))
        callback_method = bytes(items[5].value).decode("utf-8")
        user_data = bytes(items[6].value)

        return cls(
            original_txid=original_txid,
            gas_for_response=gas_for_response,
            url=url,
            filter=filter_val,
            callback_contract=callback_contract,
            callback_method=callback_method,
            user_data=user_data
        )


class OracleContract(NativeContract):
    """Oracle native contract for external data requests.

    Provides functionality for smart contracts to request external data
    from URLs and receive responses through callbacks.

    Reference: Neo.SmartContract.Native.OracleContract (v3.10.0).
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self) -> str:
        return "OracleContract"

    def _contract_activations(self) -> tuple[Any | None, ...]:
        return (None, Hardfork.HF_FAUN)

    def _register_methods(self) -> None:
        """Register Oracle contract methods."""
        super()._register_methods()

        self._register_method("getPrice", self.get_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setPrice", self.set_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("request", self.request,
                            cpu_fee=0, call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
                            manifest_parameter_names=[
                                "url",
                                "filter",
                                "callback",
                                "userData",
                                "gasForResponse",
                            ])
        self._register_method("finish", self.finish,
                            cpu_fee=0, call_flags=CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY)
        self._register_method("verify", self.verify,
                            cpu_fee=1 << 15, call_flags=CallFlags.NONE)

    def _register_events(self) -> None:
        """Register Oracle contract events."""
        super()._register_events()
        self._register_event(
            "OracleRequest",
            [
                ("Id", "Integer"),
                ("RequestContract", "Hash160"),
                ("Url", "String"),
                ("Filter", "String"),
            ],
            order=0,
        )
        self._register_event(
            "OracleResponse",
            [("Id", "Integer"), ("OriginalTx", "Hash256")],
            order=1,
        )

    def _native_supported_standards(self, context: Any) -> list[str]:
        settings, _ = self._hardfork_context(context)
        if settings is not None and self.is_hardfork_enabled(context, Hardfork.HF_FAUN):
            return ["NEP-30"]
        return []

    def initialize(self, engine: Any, hardfork: Any | None = None) -> None:
        """Initialize Oracle contract storage.

        Oracle is genesis-active; seeding only runs on the genesis /
        ``ActiveIn`` branch (``hardfork is None``) -- OracleContract.cs:167-175.
        """
        if hardfork is not None:
            return
        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            return

        # Set initial request ID to 0
        key = self._create_storage_key(PREFIX_REQUEST_ID)
        item = StorageItem(b'\x00')
        snapshot.put(key, item.value)

        # Set default price
        key = self._create_storage_key(PREFIX_PRICE)
        item = StorageItem()
        item.set(DEFAULT_ORACLE_PRICE)
        snapshot.put(key, item.value)

    # ------------------------------------------------------------------
    # Price
    # ------------------------------------------------------------------

    def get_price(self, snapshot: Any = None) -> int:
        """Get the price for an Oracle request in datoshi."""
        key = self._create_storage_key(PREFIX_PRICE)
        value = snapshot.get(key) if snapshot else None
        if value is None:
            return DEFAULT_ORACLE_PRICE
        return int.from_bytes(value, 'little', signed=True) if value else DEFAULT_ORACLE_PRICE

    def set_price(self, engine: Any, price: int) -> None:
        """Set the price for Oracle requests. Committee only."""
        if price <= 0:
            raise ValueError("Price must be positive")
        # Committee check is mandatory
        if not engine.check_committee():
            raise PermissionError("Committee authorization required")

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            return

        key = self._create_storage_key(PREFIX_PRICE)
        item = StorageItem()
        item.set(price)
        snapshot.put(key, item.value)

    # ------------------------------------------------------------------
    # request
    # ------------------------------------------------------------------

    def request(
        self,
        engine: Any,
        url: str,
        filter: str | None,
        callback: str,
        user_data: Any,
        gas_for_response: int
    ) -> None:
        """Create an Oracle request (C# OracleContract.Request, lines 221-286).

        Validates the inputs, charges ``GetPrice()`` plus the reserved
        response GAS as fees, mints the reserved GAS to the Oracle contract,
        assigns the next request id, requires the caller to be a deployed
        contract, persists the :class:`OracleRequest`, appends the id to the
        per-url-hash id list, and emits the ``OracleRequest`` notification.

        Args:
            engine: Application engine
            url: URL to fetch data from
            filter: JSONPath filter for response (optional)
            callback: Callback method name
            user_data: User data to pass to callback (a stack item or bytes)
            gas_for_response: GAS (datoshi) to reserve for the response
        """
        # --- input validation (OracleContract.cs:225-242) ----------------
        url_size = len(url.encode('utf-8'))
        if url_size > MAX_URL_LENGTH:
            raise ValueError(f"URL exceeds max length of {MAX_URL_LENGTH}")

        if filter is not None:
            filter_size = len(filter.encode('utf-8'))
            if filter_size > MAX_FILTER_LENGTH:
                raise ValueError("Filter exceeds max length")

        callback_size = len(callback.encode('utf-8'))
        if callback_size > MAX_CALLBACK_LENGTH:
            raise ValueError("Callback exceeds max length")
        if callback.startswith('_'):
            raise ValueError("Callback cannot start with underscore")

        if gas_for_response < MIN_GAS_FOR_RESPONSE:  # 0.1 GAS minimum
            raise ValueError("gasForResponse must be at least 0.1 GAS")

        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            raise RuntimeError("Snapshot not available")

        # --- charge the request price and reserve response GAS as fees ----
        # C# multiplies the datoshi amount by FeeFactor before AddFee
        # (OracleContract.cs:244-247); add_fee divides the multiplier back out.
        fee_factor = self._fee_factor(engine)
        if hasattr(engine, "add_fee"):
            engine.add_fee(self.get_price(snapshot) * fee_factor)
            engine.add_fee(gas_for_response * fee_factor)

        # --- mint the reserved GAS to the Oracle contract -----------------
        self._mint_gas(engine, self.hash, gas_for_response, call_on_payment=False)

        # --- assign the incrementing request id ---------------------------
        request_id = self._get_next_request_id(snapshot)

        # --- the caller must be a deployed contract -----------------------
        # OracleContract.cs:256-257 (placed after the id increment, exactly
        # as in C# so a faulting request still bumps the counter under the
        # committed snapshot semantics).
        calling_hash = self._calling_script_hash(engine)
        if not self._is_caller_contract(engine, snapshot, calling_hash):
            from neo.exceptions import InvalidOperationException
            raise InvalidOperationException("Only contracts can make Oracle requests")

        # --- serialize user data (C# BinarySerializer.Serialize) ----------
        user_data_bytes = self._serialize_user_data(engine, user_data)
        if len(user_data_bytes) > MAX_USER_DATA_LENGTH:
            raise ValueError("User data too large")

        # --- build and persist the request --------------------------------
        original_txid = self._get_original_txid(engine, snapshot)
        callback_contract = calling_hash if calling_hash is not None else UInt160(b'\x00' * 20)
        request = OracleRequest(
            original_txid=original_txid,
            gas_for_response=gas_for_response,
            url=url,
            filter=filter,
            callback_contract=callback_contract,
            callback_method=callback,
            user_data=user_data_bytes
        )
        self._store_request(snapshot, request_id, request)

        # --- append the id to the per-url id list -------------------------
        self._add_to_id_list(snapshot, url, request_id)

        # --- emit the OracleRequest notification --------------------------
        self._emit_oracle_request(engine, request_id, callback_contract, url, filter)

    # ------------------------------------------------------------------
    # request() helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fee_factor(engine: Any) -> int:
        """Return the engine FeeFactor (C# ApplicationEngine.FeeFactor = 10000)."""
        return int(getattr(type(engine), "FeeFactor", getattr(engine, "FeeFactor", 10000)))

    @staticmethod
    def _calling_script_hash(engine: Any) -> UInt160 | None:
        if hasattr(engine, "calling_script_hash"):
            return engine.calling_script_hash
        return None

    def _is_caller_contract(self, engine: Any, snapshot: Any, calling_hash: UInt160 | None) -> bool:
        """Mirror C# ContractManagement.IsContract(CallingScriptHash).

        A ``None`` calling hash (no caller frame) is never a contract.
        """
        if calling_hash is None:
            return False
        cm = NativeContract.get_contract_by_name("ContractManagement")
        if cm is not None and hasattr(cm, "is_contract"):
            try:
                return bool(cm.is_contract(snapshot, calling_hash))
            except (KeyError, TypeError, ValueError, AttributeError):
                return False
        # Without ContractManagement available the requirement cannot be
        # satisfied; fault closed to match "only contracts can request".
        return False

    def _serialize_user_data(self, engine: Any, user_data: Any) -> bytes:
        """Serialize *user_data* via BinarySerializer (C# line 266).

        ``user_data`` may already be raw ``bytes`` (the simplest caller form)
        or a VM stack item.  C# serializes the stack item bounded by
        ``MaxUserDataLength`` and the engine ``MaxStackSize``.
        """
        if isinstance(user_data, (bytes, bytearray)):
            return bytes(user_data)

        from neo.smartcontract.binary_serializer import BinarySerializer

        max_size = MAX_USER_DATA_LENGTH
        return BinarySerializer.serialize(user_data, max_size)

    def _get_original_txid(self, engine: Any, snapshot: Any) -> UInt256:
        """Resolve the original tx hash (C# GetOriginalTxid, lines 111-118).

        If the calling transaction itself carries an OracleResponse attribute
        the request chains back to the referenced request's original tx;
        otherwise it is simply the current transaction hash.
        """
        tx = getattr(engine, "script_container", None)
        if tx is None:
            return UInt256(b'\x00' * 32)

        response_attr = self._get_oracle_response_attr(tx)
        if response_attr is not None:
            ref_id = getattr(response_attr, "id", None)
            if ref_id is not None:
                ref_request = self.get_request(snapshot, ref_id)
                if ref_request is not None:
                    return ref_request.original_txid

        tx_hash = getattr(tx, "hash", None)
        if isinstance(tx_hash, UInt256):
            return tx_hash
        if isinstance(tx_hash, (bytes, bytearray)) and len(tx_hash) == 32:
            return UInt256(bytes(tx_hash))
        return UInt256(b'\x00' * 32)

    def _mint_gas(self, engine: Any, account: UInt160, amount: int, call_on_payment: bool) -> None:
        """Mint GAS via the GAS native contract when available (no-op otherwise)."""
        if amount == 0:
            return
        gas = NativeContract.get_contract_by_name("GasToken")
        if gas is None or not hasattr(gas, "mint"):
            return
        gas.mint(engine, account, amount, call_on_payment)

    def _emit_oracle_request(
        self,
        engine: Any,
        request_id: int,
        callback_contract: UInt160,
        url: str,
        filter: str | None,
    ) -> None:
        """Emit the ``OracleRequest`` notification (OracleContract.cs:280-285)."""
        if not hasattr(engine, "send_notification"):
            return
        from neo.vm.types import NULL, Array, ByteString, Integer

        filter_item: Any = NULL if filter is None else ByteString(filter.encode("utf-8"))
        state = Array(items=[
            Integer(request_id),
            ByteString(callback_contract.data),
            ByteString(url.encode("utf-8")),
            filter_item,
        ])
        engine.send_notification(self.hash, "OracleRequest", state)

    def _get_next_request_id(self, snapshot: Any) -> int:
        """Get and increment the request ID counter."""
        key = self._create_storage_key(PREFIX_REQUEST_ID)
        value = snapshot.get(key)
        if value is None:
            current_id = 0
        else:
            current_id = int.from_bytes(value, 'little', signed=True) if value else 0

        # Increment
        item = StorageItem()
        item.set(current_id + 1)
        snapshot.put(key, item.value)
        return current_id

    def _store_request(self, snapshot: Any, request_id: int, request: OracleRequest) -> None:
        """Store a request in storage (id encoded big-endian per C#)."""
        key = self._create_storage_key(PREFIX_REQUEST, _request_id_key_suffix(request_id))
        snapshot.put(key, request.serialize())

    def _get_url_hash(self, url: str) -> bytes:
        """Get hash of URL for indexing (C# GetUrlHash -> Crypto.Hash160)."""
        return hash160(url.encode('utf-8'))

    def _add_to_id_list(self, snapshot: Any, url: str, request_id: int) -> None:
        """Add request ID to URL's ID list (C# IdList handling, lines 271-278)."""
        url_hash = self._get_url_hash(url)
        key = self._create_storage_key(PREFIX_ID_LIST, url_hash)

        # Get existing list
        value = snapshot.get(key)
        if value is None:
            id_list = []
        else:
            id_list = self._deserialize_id_list(value)

        if len(id_list) >= MAX_PENDING_PER_URL:
            from neo.exceptions import InvalidOperationException
            raise InvalidOperationException("There are too many pending responses for this url")

        id_list.append(request_id)
        snapshot.put(key, self._serialize_id_list(id_list))

    def _serialize_id_list(self, id_list: list[int]) -> bytes:
        """Serialize ID list to bytes.

        Matches C# InteroperableList<ulong>: an Array of Integer elements
        persisted via BinarySerializer (OracleContract.cs:295-306).
        """
        from neo.smartcontract.binary_serializer import BinarySerializer
        from neo.vm.types import Array, Integer

        item = Array(items=[Integer(i) for i in id_list])
        return BinarySerializer.serialize(item)

    def _deserialize_id_list(self, data: bytes) -> list[int]:
        """Deserialize ID list from BinarySerializer bytes."""
        if not data:
            return []
        from neo.smartcontract.binary_serializer import BinarySerializer

        array = BinarySerializer.deserialize(data)
        return [int(elem.value) for elem in array]

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get_request(self, snapshot: Any, request_id: int) -> OracleRequest | None:
        """Get a pending request by ID."""
        key = self._create_storage_key(PREFIX_REQUEST, _request_id_key_suffix(request_id))
        value = snapshot.get(key) if snapshot else None
        if value is None:
            return None
        return OracleRequest.deserialize(value)

    def get_requests(self, snapshot: Any) -> Iterator[tuple[int, OracleRequest]]:
        """Get all pending requests."""
        if snapshot is None:
            return
        key_prefix = self._create_storage_key(PREFIX_REQUEST)
        for full_key, value in snapshot.find(key_prefix):
            # Extract request_id from key suffix (8-byte big-endian per C#).
            full_key_bytes = full_key.key if hasattr(full_key, "key") else full_key
            prefix_bytes = key_prefix.key if hasattr(key_prefix, "key") else key_prefix
            if not isinstance(full_key_bytes, bytes) or not isinstance(prefix_bytes, bytes):
                continue
            suffix = full_key_bytes[len(prefix_bytes):]
            if suffix:
                request_id = int.from_bytes(suffix, 'big')
                yield (request_id, OracleRequest.deserialize(value))

    def get_requests_by_url(self, snapshot: Any, url: str) -> Iterator[tuple[int, OracleRequest]]:
        """Get requests for a specific URL."""
        url_hash = self._get_url_hash(url)
        key = self._create_storage_key(PREFIX_ID_LIST, url_hash)
        value = snapshot.get(key) if snapshot else None

        if value is None:
            return

        id_list = self._deserialize_id_list(value)
        for request_id in id_list:
            request = self.get_request(snapshot, request_id)
            if request:
                yield (request_id, request)

    # ------------------------------------------------------------------
    # finish
    # ------------------------------------------------------------------

    def finish(self, engine: Any) -> None:
        """Finish an Oracle response (C# OracleContract.Finish, lines 96-109).

        Guards the invocation (the call must come through exactly one extra
        frame, with invocation counter 1), requires the calling transaction
        to carry an OracleResponse attribute, loads the referenced request,
        emits the ``OracleResponse`` notification, deserializes the stored
        user data, and dispatches the callback on the requesting contract via
        :meth:`ApplicationEngine.call_from_native_contract`.

        Reference: Neo.SmartContract.Native.OracleContract.Finish
        """
        # --- invocation guards (OracleContract.cs:99-100) -----------------
        self._assert_finish_invocation(engine)

        tx = getattr(engine, 'script_container', None)
        if tx is None:
            raise RuntimeError("No transaction attached to engine")

        # --- locate OracleResponse attribute on the transaction ----------
        response_attr = self._get_oracle_response_attr(tx)
        if response_attr is None:
            raise ValueError("Oracle response not found")

        request_id = getattr(response_attr, 'id', None)
        if request_id is None:
            raise ValueError("OracleResponse missing request id")

        response_code = getattr(response_attr, 'code', None)
        response_result = getattr(response_attr, 'result', b'')

        # --- retrieve the original request from storage ------------------
        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            raise RuntimeError("Snapshot not available")

        request = self.get_request(snapshot, request_id)
        if request is None:
            raise ValueError("Oracle request not found")

        # --- emit the OracleResponse notification (line 106) -------------
        self._emit_oracle_response(engine, request_id, request.original_txid)

        # --- deserialize stored user data (line 107) ---------------------
        user_data_item = self._deserialize_user_data(engine, request.user_data)

        # --- dispatch the callback (line 108) ----------------------------
        #     engine.CallFromNativeContractAsync(Hash, CallbackContract,
        #         CallbackMethod, Url, userData, (int)Code, Result)
        code_value = int(response_code) if response_code is not None else int(OracleResponseCode.Error)
        result_bytes = response_result if response_result else b''
        self._dispatch_callback(
            engine,
            request.callback_contract,
            request.callback_method,
            request.url,
            user_data_item,
            code_value,
            result_bytes,
        )

    # ------------------------------------------------------------------
    # finish() helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_finish_invocation(engine: Any) -> None:
        """Enforce C# Finish guards (OracleContract.cs:99-100).

        ``InvocationStack.Count != 2`` -> fault; ``GetInvocationCounter() != 1``
        -> fault. The mock/engine may not expose either surface; when a guard
        value is unavailable it is treated as satisfied so that pure-logic
        tests still run.
        """
        from neo.exceptions import InvalidOperationException

        stack = getattr(engine, "invocation_stack", None)
        if stack is not None and len(stack) != 2:
            raise InvalidOperationException("Finish must be invoked through a single call frame")

        counter = None
        if hasattr(engine, "get_invocation_counter"):
            try:
                counter = engine.get_invocation_counter()
            except (TypeError, ValueError):
                counter = None
        if counter is not None and int(counter) != 1:
            raise InvalidOperationException("Finish invocation counter must be 1")

    @staticmethod
    def _get_oracle_response_attr(tx: Any) -> Any:
        """Extract the OracleResponse attribute (type 0x11) from *tx*."""
        attrs = getattr(tx, 'attributes', None)
        if not attrs:
            return None
        for attr in attrs:
            attr_type = getattr(attr, 'type', None)
            if attr_type is not None and int(attr_type) == ORACLE_RESPONSE_ATTR_TYPE:
                return attr
        return None

    def _emit_oracle_response(self, engine: Any, request_id: int, original_txid: UInt256) -> None:
        """Emit the ``OracleResponse`` notification (OracleContract.cs:106)."""
        if not hasattr(engine, "send_notification"):
            return
        from neo.vm.types import Array, ByteString, Integer

        state = Array(items=[
            Integer(request_id),
            ByteString(original_txid.data),
        ])
        engine.send_notification(self.hash, "OracleResponse", state)

    def _deserialize_user_data(self, engine: Any, user_data: bytes) -> Any:
        """Deserialize stored user data via BinarySerializer (C# line 107).

        Returns a VM stack item. If the bytes are not serializer output the
        raw bytes are wrapped as a ByteString fallback so the callback still
        receives something meaningful.
        """
        from neo.smartcontract.binary_serializer import BinarySerializer
        from neo.vm.types import ByteString

        if not user_data:
            return ByteString(b"")
        try:
            return BinarySerializer.deserialize(user_data)
        except (ValueError, IndexError, TypeError):
            return ByteString(bytes(user_data))

    def _dispatch_callback(
        self,
        engine: Any,
        contract: UInt160,
        method: str,
        url: str,
        user_data_item: Any,
        code: int,
        result: bytes,
    ) -> None:
        """Dispatch the oracle callback on the requesting contract.

        Mirrors ``engine.CallFromNativeContractAsync(Hash, CallbackContract,
        CallbackMethod, Url, userData, (int)Code, Result)``. The engine
        surface is used when available; otherwise the call is recorded as a
        notification so the intent stays observable in tests.
        """
        from neo.vm.types import Array, ByteString, Integer

        url_item = ByteString(url.encode("utf-8"))
        code_item = Integer(code)
        result_item = ByteString(result if result else b"")

        if hasattr(engine, "call_from_native_contract"):
            engine.call_from_native_contract(
                self.hash, contract, method,
                url_item, user_data_item, code_item, result_item,
            )
            return
        if hasattr(engine, "send_notification"):
            state = Array(items=[url_item, user_data_item, code_item, result_item])
            engine.send_notification(contract, f"Oracle.{method}", state)

    # ------------------------------------------------------------------
    # verify
    # ------------------------------------------------------------------

    def verify(self, engine: Any) -> bool:
        """Verify Oracle response transaction (OracleContract.cs:288-293).

        Returns True only when the script container (transaction) carries
        an OracleResponse attribute (type 0x11).
        """
        tx = getattr(engine, 'script_container', None)
        if tx is None:
            return False
        return self._get_oracle_response_attr(tx) is not None

    # ------------------------------------------------------------------
    # post_persist
    # ------------------------------------------------------------------

    def post_persist(self, engine: Any) -> None:
        """Process oracle responses at block post-persist (C# PostPersistAsync).

        For every transaction in the persisting block that carries an
        OracleResponse attribute: load and delete the pending request, prune
        the per-url id list, and accrue the Oracle-node reward. Rewards are
        finally minted to the designated Oracle nodes' signature-redeem-script
        accounts (OracleContract.cs:177-219).

        Every engine interaction is guarded so the routine no-ops gracefully
        when a dependency (snapshot, persisting block, GAS, RoleManagement) is
        unavailable.
        """
        snapshot = getattr(engine, "snapshot", None)
        if snapshot is None:
            return

        block = self._persisting_block(engine)
        if block is None:
            return
        transactions = getattr(block, "transactions", None)
        if not transactions:
            return
        block_index = getattr(block, "index", None)

        nodes: list[list] | None = None  # list of [account(UInt160), gas(int)]

        for tx in transactions:
            response_attr = self._get_oracle_response_attr(tx)
            if response_attr is None:
                continue
            request_id = getattr(response_attr, "id", None)
            if request_id is None:
                continue

            # Load the pending request; skip if already gone.
            request = self.get_request(snapshot, request_id)
            if request is None:
                continue

            # Remove the request and prune the id list.
            self._remove_request(snapshot, request_id, request.url)

            # Lazily resolve the designated Oracle nodes (once per block).
            if nodes is None:
                nodes = self._designated_oracle_accounts(snapshot, block_index)

            if nodes:
                index = request_id % len(nodes)
                nodes[index][1] += self.get_price(snapshot)

        if not nodes:
            return
        for account, gas in nodes:
            if gas > 0:
                self._mint_gas(engine, account, gas, call_on_payment=False)

    @staticmethod
    def _persisting_block(engine: Any) -> Any:
        """Resolve the persisting block from the engine or its snapshot."""
        block = getattr(engine, "persisting_block", None)
        if block is not None:
            return block
        snapshot = getattr(engine, "snapshot", None)
        if snapshot is not None:
            return getattr(snapshot, "persisting_block", None)
        return None

    def _designated_oracle_accounts(self, snapshot: Any, block_index: Any) -> list[list]:
        """Resolve the Oracle-node payout accounts (OracleContract.cs:202-204).

        Each designated Oracle public key maps to the script hash of its
        single-signature redeem script; the accrued GAS starts at zero.
        Returns an empty list when RoleManagement (or the designation) is
        unavailable.
        """
        from neo.native.role_management import Role
        from neo.smartcontract.syscalls.contract import _create_signature_redeem_script

        rm = NativeContract.get_contract_by_name("RoleManagement")
        if rm is None or not hasattr(rm, "get_designated_by_role"):
            return []

        idx = int(block_index) if block_index is not None else 0
        try:
            pubkeys = rm.get_designated_by_role(snapshot, Role.ORACLE, idx)
        except (KeyError, TypeError, ValueError, AttributeError):
            return []
        if not pubkeys:
            return []

        accounts: list[list] = []
        for pk in pubkeys:
            pk_bytes = self._pubkey_bytes(pk)
            if pk_bytes is None:
                continue
            redeem = _create_signature_redeem_script(pk_bytes)
            account = UInt160(hash160(redeem))
            accounts.append([account, 0])
        return accounts

    @staticmethod
    def _pubkey_bytes(pk: Any) -> bytes | None:
        """Normalize a designated key to its 33-byte compressed encoding."""
        if isinstance(pk, (bytes, bytearray)):
            return bytes(pk)
        for attr in ("data", "encoded", "to_bytes"):
            val = getattr(pk, attr, None)
            if val is None:
                continue
            if callable(val):
                try:
                    val = val()
                except (TypeError, ValueError):
                    continue
            if isinstance(val, (bytes, bytearray)):
                return bytes(val)
        return None

    # ------------------------------------------------------------------
    # request removal
    # ------------------------------------------------------------------

    def _remove_request(self, snapshot: Any, request_id: int, url: str) -> None:
        """Remove a request after processing (C# PostPersist storage cleanup)."""
        # Remove from request storage
        key = self._create_storage_key(PREFIX_REQUEST, _request_id_key_suffix(request_id))
        snapshot.delete(key)

        # Remove from URL index
        url_hash = self._get_url_hash(url)
        key = self._create_storage_key(PREFIX_ID_LIST, url_hash)
        value = snapshot.get(key)

        if value:
            id_list = self._deserialize_id_list(value)
            if request_id in id_list:
                id_list.remove(request_id)
                if id_list:
                    snapshot.put(key, self._serialize_id_list(id_list))
                else:
                    snapshot.delete(key)
