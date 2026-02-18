"""Oracle contract for external data requests.

Reference: Neo.SmartContract.Native.OracleContract
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

# Storage prefixes
PREFIX_PRICE = 5
PREFIX_REQUEST_ID = 9
PREFIX_REQUEST = 7
PREFIX_ID_LIST = 6

# Limits
MAX_URL_LENGTH = 256
MAX_FILTER_LENGTH = 128
MAX_CALLBACK_LENGTH = 32
MAX_USER_DATA_LENGTH = 512

# Default oracle price (0.5 GAS in datoshi)
DEFAULT_ORACLE_PRICE = 50_000_000

# OracleResponse transaction attribute type code
ORACLE_RESPONSE_ATTR_TYPE = 0x11

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

@dataclass
class OracleRequest:
    """Oracle request data structure."""

    original_txid: UInt256 = field(default_factory=lambda: UInt256(b'\x00' * 32))
    gas_for_response: int = 0
    url: str = ""
    filter: str | None = None
    callback_contract: UInt160 = field(default_factory=lambda: UInt160(b'\x00' * 20))
    callback_method: str = ""
    user_data: bytes = b""
    
    def serialize(self) -> bytes:
        """Serialize request to bytes."""
        # Validate field lengths before serialization
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

        result = bytearray()
        
        # Original txid (32 bytes)
        result.extend(self.original_txid.data)
        
        # Gas for response (8 bytes, little-endian)
        result.extend(self.gas_for_response.to_bytes(8, 'little'))
        
        # URL (variable-length encoded)
        if len(url_bytes) < 0xFD:
            result.append(len(url_bytes))
        elif len(url_bytes) <= 0xFFFF:
            result.append(0xFD)
            result.extend(len(url_bytes).to_bytes(2, 'little'))
        else:
            result.append(0xFE)
            result.extend(len(url_bytes).to_bytes(4, 'little'))
        result.extend(url_bytes)
        
        # Filter (length-prefixed, 0 for None)
        if self.filter is None:
            result.append(0)
        else:
            filter_bytes = self.filter.encode('utf-8')
            result.append(len(filter_bytes))
            result.extend(filter_bytes)
        
        # Callback contract (20 bytes)
        result.extend(self.callback_contract.data)
        
        # Callback method (length-prefixed)
        result.append(len(method_bytes))
        result.extend(method_bytes)
        
        # User data (length-prefixed)
        result.append(len(self.user_data) & 0xff)
        result.append((len(self.user_data) >> 8) & 0xff)
        result.extend(self.user_data)
        
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> OracleRequest:
        """Deserialize request from bytes."""
        offset = 0
        
        # Original txid
        original_txid = UInt256(data[offset:offset + 32])
        offset += 32
        
        # Gas for response
        gas_for_response = int.from_bytes(data[offset:offset + 8], 'little')
        offset += 8
        
        # URL (var-int length)
        first_byte = data[offset]
        offset += 1
        if first_byte < 0xFD:
            url_len = first_byte
        elif first_byte == 0xFD:
            url_len = int.from_bytes(data[offset:offset + 2], 'little')
            offset += 2
        elif first_byte == 0xFE:
            url_len = int.from_bytes(data[offset:offset + 4], 'little')
            offset += 4
        else:
            url_len = int.from_bytes(data[offset:offset + 8], 'little')
            offset += 8
        url = data[offset:offset + url_len].decode('utf-8')
        offset += url_len
        
        # Filter
        filter_len = data[offset]
        offset += 1
        if filter_len == 0:
            filter_val = None
        else:
            filter_val = data[offset:offset + filter_len].decode('utf-8')
            offset += filter_len
        
        # Callback contract
        callback_contract = UInt160(data[offset:offset + 20])
        offset += 20
        
        # Callback method
        method_len = data[offset]
        offset += 1
        callback_method = data[offset:offset + method_len].decode('utf-8')
        offset += method_len
        
        # User data
        user_data_len = data[offset] | (data[offset + 1] << 8)
        offset += 2
        user_data = data[offset:offset + user_data_len]
        
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
    
    def initialize(self, engine: Any) -> None:
        """Initialize Oracle contract storage."""
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
    
    def request(
        self,
        engine: Any,
        url: str,
        filter: str | None,
        callback: str,
        user_data: Any,
        gas_for_response: int
    ) -> None:
        """Create an Oracle request.
        
        Args:
            engine: Application engine
            url: URL to fetch data from
            filter: JSONPath filter for response
            callback: Callback method name
            user_data: User data to pass to callback
            gas_for_response: GAS to reserve for response
        """
        # Validate URL
        url_size = len(url.encode('utf-8'))
        if url_size > MAX_URL_LENGTH:
            raise ValueError(f"URL exceeds max length of {MAX_URL_LENGTH}")
        
        # Validate filter
        if filter is not None:
            filter_size = len(filter.encode('utf-8'))
            if filter_size > MAX_FILTER_LENGTH:
                raise ValueError("Filter exceeds max length")
        
        # Validate callback
        callback_size = len(callback.encode('utf-8'))
        if callback_size > MAX_CALLBACK_LENGTH:
            raise ValueError("Callback exceeds max length")
        if callback.startswith('_'):
            raise ValueError("Callback cannot start with underscore")
        
        # Validate gas
        if gas_for_response < 10_000_000:  # 0.1 GAS minimum
            raise ValueError("gasForResponse must be at least 0.1 GAS")
        
        snapshot = engine.snapshot if hasattr(engine, 'snapshot') else None
        if snapshot is None:
            raise RuntimeError("Snapshot not available")

        # Get and increment request ID
        request_id = self._get_next_request_id(snapshot)

        # Serialize user data
        if isinstance(user_data, bytes):
            user_data_bytes = user_data
        else:
            user_data_bytes = b''

        if len(user_data_bytes) > MAX_USER_DATA_LENGTH:
            raise ValueError("User data too large")

        # Create request
        original_txid = (
            engine.script_container.hash
            if hasattr(engine, 'script_container') and hasattr(engine.script_container, 'hash')
            else UInt256(b'\x00' * 32)
        )
        callback_contract = (
            engine.calling_script_hash
            if hasattr(engine, 'calling_script_hash')
            else UInt160(b'\x00' * 20)
        )
        request = OracleRequest(
            original_txid=original_txid,
            gas_for_response=gas_for_response,
            url=url,
            filter=filter,
            callback_contract=callback_contract,
            callback_method=callback,
            user_data=user_data_bytes
        )

        # Store request
        self._store_request(snapshot, request_id, request)

        # Add to URL index
        self._add_to_id_list(snapshot, url, request_id)
    
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
        """Store a request in storage."""
        key = self._create_storage_key(PREFIX_REQUEST, request_id)
        snapshot.put(key, request.serialize())
    
    def _get_url_hash(self, url: str) -> bytes:
        """Get hash of URL for indexing."""
        return hash160(url.encode('utf-8'))
    
    def _add_to_id_list(self, snapshot: Any, url: str, request_id: int) -> None:
        """Add request ID to URL's ID list."""
        url_hash = self._get_url_hash(url)
        key = self._create_storage_key(PREFIX_ID_LIST, url_hash)

        # Get existing list
        value = snapshot.get(key)
        if value is None:
            id_list = []
        else:
            id_list = self._deserialize_id_list(value)

        if len(id_list) >= 256:
            raise ValueError("Too many pending responses for URL")

        id_list.append(request_id)
        snapshot.put(key, self._serialize_id_list(id_list))
    
    def _serialize_id_list(self, id_list: list[int]) -> bytes:
        """Serialize ID list to bytes."""
        result = bytearray()
        result.append(len(id_list))
        for id_val in id_list:
            result.extend(id_val.to_bytes(8, 'little'))
        return bytes(result)
    
    def _deserialize_id_list(self, data: bytes) -> list[int]:
        """Deserialize ID list from bytes."""
        if not data:
            return []
        count = data[0]
        result = []
        for i in range(count):
            offset = 1 + i * 8
            result.append(int.from_bytes(data[offset:offset + 8], 'little'))
        return result
    
    def get_request(self, snapshot: Any, request_id: int) -> OracleRequest | None:
        """Get a pending request by ID."""
        key = self._create_storage_key(PREFIX_REQUEST, request_id)
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
            # Extract request_id from key suffix
            full_key_bytes = full_key.key if hasattr(full_key, "key") else full_key
            prefix_bytes = key_prefix.key if hasattr(key_prefix, "key") else key_prefix
            if not isinstance(full_key_bytes, bytes) or not isinstance(prefix_bytes, bytes):
                continue
            suffix = full_key_bytes[len(prefix_bytes):]
            if suffix:
                request_id = int.from_bytes(suffix, 'little')
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
    
    def finish(self, engine: Any) -> None:
        """Finish an Oracle response.

        Called by Oracle nodes to deliver response data.  The transaction
        must carry an OracleResponse attribute (type 0x11) whose fields
        provide ``id``, ``code``, and ``result``.

        Reference: Neo.SmartContract.Native.OracleContract.Finish
        """
        tx = getattr(engine, 'script_container', None)
        if tx is None:
            raise RuntimeError("No transaction attached to engine")

        # --- locate OracleResponse attribute on the transaction ----------
        response_attr = self._get_oracle_response_attr(tx)
        if response_attr is None:
            raise ValueError("Transaction has no OracleResponse attribute")

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
            raise ValueError(f"Oracle request {request_id} not found")

        # --- remove the fulfilled request --------------------------------
        self._remove_request(snapshot, request_id, request.url)

        # --- refund unused GAS to the original requester -----------------
        #     In the full C# implementation the fixed response-tx cost is
        #     deducted and the remainder is sent back.  For this reference
        #     spec we transfer the full gas_for_response back to the
        #     requester via GasToken when available.
        if request.gas_for_response > 0:
            gas_contract = NativeContract.get_contract_by_name("GasToken")
            if gas_contract is not None and hasattr(gas_contract, 'mint'):
                gas_contract.mint(
                    engine,
                    request.callback_contract,
                    request.gas_for_response,
                )

        # --- invoke the callback on the requesting contract --------------
        #     A production node would use System.Contract.Call to invoke
        #     callback_contract.callback_method(url, user_data, code, result).
        #     Here we record the intent so tests can observe it.
        if request.callback_contract != UInt160(b'\x00' * 20) and request.callback_method:
            self._invoke_callback(
                engine,
                request.callback_contract,
                request.callback_method,
                request.url,
                request.user_data,
                response_code,
                response_result,
            )

    # ------------------------------------------------------------------
    # finish() helpers
    # ------------------------------------------------------------------

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

    def _invoke_callback(
        self,
        engine: Any,
        contract: UInt160,
        method: str,
        url: str,
        user_data: bytes,
        code: Any,
        result: bytes,
    ) -> None:
        """Invoke the oracle callback on the requesting contract.

        In a full node this dispatches via ``System.Contract.Call``.
        For the reference spec we attempt ``engine.contract_call`` when
        available, otherwise we record the pending callback as a
        notification so the intent is observable.
        """
        if hasattr(engine, 'contract_call'):
            engine.contract_call(contract, method, [url, user_data, code, result])
        elif hasattr(engine, 'send_notification'):
            from neo.vm.types import Array, ByteString, Integer
            state = Array(items=[
                ByteString(url.encode('utf-8')),
                ByteString(user_data),
                Integer(int(code) if code is not None else 0xff),
                ByteString(result if result else b''),
            ])
            engine.send_notification(contract, f"Oracle.{method}", state)
    
    def verify(self, engine: Any) -> bool:
        """Verify Oracle response transaction.

        Returns True only when the script container (transaction) carries
        an OracleResponse attribute (type 0x11).
        """
        tx = getattr(engine, 'script_container', None)
        if tx is None:
            return False

        attrs = getattr(tx, 'attributes', None)
        if not attrs:
            return False

        for attr in attrs:
            attr_type = getattr(attr, 'type', None)
            if attr_type is not None and int(attr_type) == ORACLE_RESPONSE_ATTR_TYPE:
                return True

        return False
    
    def _remove_request(self, snapshot: Any, request_id: int, url: str) -> None:
        """Remove a request after processing."""
        # Remove from request storage
        key = self._create_storage_key(PREFIX_REQUEST, request_id)
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
