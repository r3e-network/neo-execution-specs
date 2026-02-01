"""Oracle contract for external data requests.

Reference: Neo.SmartContract.Native.OracleContract
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, Iterator, List, Optional, Tuple

from neo.types import UInt160, UInt256
from neo.native.native_contract import NativeContract, CallFlags, StorageKey, StorageItem
from neo.crypto import hash160


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
    filter: Optional[str] = None
    callback_contract: UInt160 = field(default_factory=lambda: UInt160(b'\x00' * 20))
    callback_method: str = ""
    user_data: bytes = b""
    
    def serialize(self) -> bytes:
        """Serialize request to bytes."""
        result = bytearray()
        
        # Original txid (32 bytes)
        result.extend(self.original_txid.data)
        
        # Gas for response (8 bytes, little-endian)
        result.extend(self.gas_for_response.to_bytes(8, 'little'))
        
        # URL (length-prefixed)
        url_bytes = self.url.encode('utf-8')
        result.append(len(url_bytes))
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
        method_bytes = self.callback_method.encode('utf-8')
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
        
        # URL
        url_len = data[offset]
        offset += 1
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
        self._storage: Dict[bytes, StorageItem] = {}
        super().__init__()
    
    @property
    def name(self) -> str:
        return "OracleContract"
    
    def _register_methods(self) -> None:
        """Register Oracle contract methods."""
        super()._register_methods()
        
        self._register_method("getPrice", self.get_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setPrice", self.set_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("request", self.request,
                            cpu_fee=0, call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY)
        self._register_method("finish", self.finish,
                            cpu_fee=0, call_flags=CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY)
        self._register_method("verify", self.verify,
                            cpu_fee=1 << 15, call_flags=CallFlags.NONE)
    
    def initialize(self, engine: Any) -> None:
        """Initialize Oracle contract storage."""
        # Set initial request ID to 0
        key = self._create_storage_key(PREFIX_REQUEST_ID)
        self._storage[key.key] = StorageItem(b'\x00')
        
        # Set default price
        key = self._create_storage_key(PREFIX_PRICE)
        self._storage[key.key] = StorageItem()
        self._storage[key.key].set(DEFAULT_ORACLE_PRICE)
    
    def get_price(self, snapshot: Any = None) -> int:
        """Get the price for an Oracle request in datoshi."""
        key = self._create_storage_key(PREFIX_PRICE)
        item = self._storage.get(key.key)
        if item is None:
            return DEFAULT_ORACLE_PRICE
        return int(item)
    
    def set_price(self, engine: Any, price: int) -> None:
        """Set the price for Oracle requests. Committee only."""
        if price <= 0:
            raise ValueError("Price must be positive")
        
        key = self._create_storage_key(PREFIX_PRICE)
        if key.key not in self._storage:
            self._storage[key.key] = StorageItem()
        self._storage[key.key].set(price)
    
    def request(
        self,
        engine: Any,
        url: str,
        filter: Optional[str],
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
                raise ValueError(f"Filter exceeds max length")
        
        # Validate callback
        callback_size = len(callback.encode('utf-8'))
        if callback_size > MAX_CALLBACK_LENGTH:
            raise ValueError(f"Callback exceeds max length")
        if callback.startswith('_'):
            raise ValueError("Callback cannot start with underscore")
        
        # Validate gas
        if gas_for_response < 10_000_000:  # 0.1 GAS minimum
            raise ValueError("gasForResponse must be at least 0.1 GAS")
        
        # Get and increment request ID
        request_id = self._get_next_request_id()
        
        # Serialize user data
        if isinstance(user_data, bytes):
            user_data_bytes = user_data
        else:
            user_data_bytes = b''
        
        if len(user_data_bytes) > MAX_USER_DATA_LENGTH:
            raise ValueError("User data too large")
        
        # Create request
        request = OracleRequest(
            original_txid=UInt256(b'\x00' * 32),
            gas_for_response=gas_for_response,
            url=url,
            filter=filter,
            callback_contract=UInt160(b'\x00' * 20),
            callback_method=callback,
            user_data=user_data_bytes
        )
        
        # Store request
        self._store_request(request_id, request)
        
        # Add to URL index
        self._add_to_id_list(url, request_id)
    
    def _get_next_request_id(self) -> int:
        """Get and increment the request ID counter."""
        key = self._create_storage_key(PREFIX_REQUEST_ID)
        item = self._storage.get(key.key)
        if item is None:
            current_id = 0
        else:
            current_id = int(item)
        
        # Increment
        self._storage[key.key] = StorageItem()
        self._storage[key.key].set(current_id + 1)
        return current_id
    
    def _store_request(self, request_id: int, request: OracleRequest) -> None:
        """Store a request in storage."""
        key = self._create_storage_key(PREFIX_REQUEST, request_id)
        self._storage[key.key] = StorageItem(request.serialize())
    
    def _get_url_hash(self, url: str) -> bytes:
        """Get hash of URL for indexing."""
        return hash160(url.encode('utf-8'))
    
    def _add_to_id_list(self, url: str, request_id: int) -> None:
        """Add request ID to URL's ID list."""
        url_hash = self._get_url_hash(url)
        key = self._create_storage_key(PREFIX_ID_LIST, url_hash)
        
        # Get existing list
        item = self._storage.get(key.key)
        if item is None:
            id_list = []
        else:
            id_list = self._deserialize_id_list(item.value)
        
        if len(id_list) >= 256:
            raise ValueError("Too many pending responses for URL")
        
        id_list.append(request_id)
        self._storage[key.key] = StorageItem(self._serialize_id_list(id_list))
    
    def _serialize_id_list(self, id_list: List[int]) -> bytes:
        """Serialize ID list to bytes."""
        result = bytearray()
        result.append(len(id_list))
        for id_val in id_list:
            result.extend(id_val.to_bytes(8, 'little'))
        return bytes(result)
    
    def _deserialize_id_list(self, data: bytes) -> List[int]:
        """Deserialize ID list from bytes."""
        if not data:
            return []
        count = data[0]
        result = []
        for i in range(count):
            offset = 1 + i * 8
            result.append(int.from_bytes(data[offset:offset + 8], 'little'))
        return result
    
    def get_request(self, snapshot: Any, request_id: int) -> Optional[OracleRequest]:
        """Get a pending request by ID."""
        key = self._create_storage_key(PREFIX_REQUEST, request_id)
        item = self._storage.get(key.key)
        if item is None:
            return None
        return OracleRequest.deserialize(item.value)
    
    def get_requests(self, snapshot: Any) -> Iterator[Tuple[int, OracleRequest]]:
        """Get all pending requests."""
        prefix = bytes([PREFIX_REQUEST])
        for key, item in self._storage.items():
            if key.startswith(prefix):
                request_id = int.from_bytes(key[1:], 'big')
                yield (request_id, OracleRequest.deserialize(item.value))
    
    def get_requests_by_url(self, snapshot: Any, url: str) -> Iterator[Tuple[int, OracleRequest]]:
        """Get requests for a specific URL."""
        url_hash = self._get_url_hash(url)
        key = self._create_storage_key(PREFIX_ID_LIST, url_hash)
        item = self._storage.get(key.key)
        
        if item is None:
            return
        
        id_list = self._deserialize_id_list(item.value)
        for request_id in id_list:
            request = self.get_request(snapshot, request_id)
            if request:
                yield (request_id, request)
    
    def finish(self, engine: Any) -> None:
        """Finish an Oracle response.
        
        Called by Oracle nodes to deliver response data.
        """
        # This would be called with response data
        # In full implementation, validates and processes response
        pass
    
    def verify(self, engine: Any) -> bool:
        """Verify Oracle response transaction.
        
        Returns True if transaction has OracleResponse attribute.
        """
        # In full implementation, checks for OracleResponse attribute
        return True
    
    def _remove_request(self, request_id: int, url: str) -> None:
        """Remove a request after processing."""
        # Remove from request storage
        key = self._create_storage_key(PREFIX_REQUEST, request_id)
        if key.key in self._storage:
            del self._storage[key.key]
        
        # Remove from URL index
        url_hash = self._get_url_hash(url)
        key = self._create_storage_key(PREFIX_ID_LIST, url_hash)
        item = self._storage.get(key.key)
        
        if item:
            id_list = self._deserialize_id_list(item.value)
            if request_id in id_list:
                id_list.remove(request_id)
                if id_list:
                    self._storage[key.key] = StorageItem(
                        self._serialize_id_list(id_list)
                    )
                else:
                    del self._storage[key.key]
