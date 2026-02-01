"""Oracle contract for external data requests."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from neo.types import UInt160, UInt256
from neo.native.native_contract import NativeContract, CallFlags, StorageItem


# Storage prefixes
PREFIX_PRICE = 5
PREFIX_REQUEST_ID = 9
PREFIX_REQUEST = 7
PREFIX_ID_LIST = 6

# Default oracle price (0.5 GAS)
DEFAULT_ORACLE_PRICE = 50000000


@dataclass
class OracleRequest:
    """Oracle request data."""
    original_txid: Optional[UInt256] = None
    gas_for_response: int = 0
    url: str = ""
    filter: Optional[str] = None
    callback_contract: Optional[UInt160] = None
    callback_method: str = ""
    user_data: bytes = b""
