"""Syscall implementations."""

from .runtime import *
from .storage import *
from .crypto import *
from .contract import *
from .iterator import *

__all__ = [
    # Runtime
    "runtime_get_trigger",
    "runtime_get_time",
    # Storage
    "storage_get",
    "storage_put",
    # Crypto
    "crypto_check_sig",
    "crypto_check_multisig",
    # Contract
    "contract_call",
    "contract_call_native",
    "contract_get_call_flags",
    "contract_create_standard_account",
    "contract_create_multisig_account",
    # Iterator
    "iterator_next",
    "iterator_value",
]
