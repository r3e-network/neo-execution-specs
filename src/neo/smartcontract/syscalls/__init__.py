"""Syscall implementations."""

from neo.smartcontract.syscalls.runtime import (
    runtime_get_trigger,
    runtime_get_time,
    runtime_platform,
    runtime_get_network,
    runtime_log,
    runtime_notify,
    runtime_check_witness,
    runtime_gas_left,
    runtime_get_script_container,
    runtime_get_executing_script_hash,
    runtime_get_calling_script_hash,
    runtime_get_entry_script_hash,
    runtime_get_random,
    runtime_get_address_version,
    runtime_get_notifications,
    runtime_burn_gas,
    runtime_get_invocation_counter,
)
from neo.smartcontract.syscalls.storage import (
    storage_get_context,
    storage_get_read_only_context,
    storage_as_read_only,
    storage_get,
    storage_put,
    storage_delete,
    storage_find,
)
from neo.smartcontract.syscalls.crypto import (
    crypto_check_sig,
    crypto_check_multisig,
)
from neo.smartcontract.syscalls.contract import (
    contract_call,
    contract_call_native,
    contract_get_call_flags,
    contract_create_standard_account,
    contract_create_multisig_account,
)
from neo.smartcontract.syscalls.iterator import (
    iterator_next,
    iterator_value,
)

__all__ = [
    # Runtime
    "runtime_get_trigger",
    "runtime_get_time",
    "runtime_platform",
    "runtime_get_network",
    "runtime_log",
    "runtime_notify",
    "runtime_check_witness",
    "runtime_gas_left",
    "runtime_get_script_container",
    "runtime_get_executing_script_hash",
    "runtime_get_calling_script_hash",
    "runtime_get_entry_script_hash",
    "runtime_get_random",
    "runtime_get_address_version",
    "runtime_get_notifications",
    "runtime_burn_gas",
    "runtime_get_invocation_counter",
    # Storage
    "storage_get_context",
    "storage_get_read_only_context",
    "storage_as_read_only",
    "storage_get",
    "storage_put",
    "storage_delete",
    "storage_find",
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
