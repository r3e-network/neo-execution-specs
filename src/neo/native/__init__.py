"""Native contracts."""

from .native_contract import NativeContract, CallFlags, StorageKey, StorageItem
from .contract_management import ContractManagement
from .std_lib import StdLib
from .crypto_lib import CryptoLib, NamedCurveHash
from .ledger import LedgerContract
from .neo_token import NeoToken
from .gas_token import GasToken
from .policy import PolicyContract
from .role_management import RoleManagement, Role
from .oracle import OracleContract, OracleRequest, OracleResponseCode
from .notary import Notary, Deposit

__all__ = [
    "NativeContract",
    "CallFlags",
    "StorageKey",
    "StorageItem",
    "ContractManagement",
    "StdLib",
    "CryptoLib",
    "NamedCurveHash",
    "LedgerContract",
    "NeoToken",
    "GasToken",
    "PolicyContract",
    "RoleManagement",
    "Role",
    "OracleContract",
    "OracleRequest",
    "OracleResponseCode",
    "Notary",
    "Deposit",
    "initialize_native_contracts",
]


def initialize_native_contracts() -> dict:
    """Instantiate all native contracts in Neo C# v3.9.1 order.

    Resets the ID counter and registries so that each contract receives
    the deterministic ID assigned by the reference implementation.

    Returns:
        Dict mapping contract name to instance.
    """
    # Reset registries for deterministic re-initialization
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0

    # Instantiation order matches Neo C# v3.9.1
    contracts = {
        "ContractManagement": ContractManagement(),   # -1
        "StdLib": StdLib(),                           # -2
        "CryptoLib": CryptoLib(),                     # -3
        "LedgerContract": LedgerContract(),           # -4
        "NeoToken": NeoToken(),                       # -5
        "GasToken": GasToken(),                       # -6
        "PolicyContract": PolicyContract(),           # -7
        "RoleManagement": RoleManagement(),           # -8
        "OracleContract": OracleContract(),           # -9
        "Notary": Notary(),                           # -10
    }
    return contracts
