"""Lock native method surface to Neo v3.9.1 method names."""

import inspect
import json
from types import SimpleNamespace

from neo.hardfork import Hardfork
from neo.native import initialize_native_contracts
from neo.native.native_contract import CallFlags, NativeContract
from neo.protocol_settings import ProtocolSettings


EXPECTED_METHODS_V391: dict[str, set[str]] = {
    "ContractManagement": {
        "deploy",
        "destroy",
        "getContract",
        "getContractById",
        "getContractHashes",
        "getMinimumDeploymentFee",
        "hasMethod",
        "isContract",
        "setMinimumDeploymentFee",
        "update",
    },
    "StdLib": {
        "atoi",
        "base58CheckDecode",
        "base58CheckEncode",
        "base58Decode",
        "base58Encode",
        "base64Decode",
        "base64Encode",
        "base64UrlDecode",
        "base64UrlEncode",
        "deserialize",
        "hexDecode",
        "hexEncode",
        "itoa",
        "jsonDeserialize",
        "jsonSerialize",
        "memoryCompare",
        "memorySearch",
        "serialize",
        "strLen",
        "stringSplit",
    },
    "CryptoLib": {
        "bls12381Add",
        "bls12381Deserialize",
        "bls12381Equal",
        "bls12381Mul",
        "bls12381Pairing",
        "bls12381Serialize",
        "keccak256",
        "murmur32",
        "recoverSecp256K1",
        "ripemd160",
        "sha256",
        "verifyWithECDsa",
        "verifyWithEd25519",
    },
    "LedgerContract": {
        "currentHash",
        "currentIndex",
        "getBlock",
        "getTransaction",
        "getTransactionFromBlock",
        "getTransactionHeight",
        "getTransactionSigners",
        "getTransactionVMState",
    },
    "NeoToken": {
        "balanceOf",
        "decimals",
        "getAccountState",
        "getAllCandidates",
        "getCandidateVote",
        "getCandidates",
        "getCommittee",
        "getCommitteeAddress",
        "getGasPerBlock",
        "getNextBlockValidators",
        "getRegisterPrice",
        "onNEP17Payment",
        "registerCandidate",
        "setGasPerBlock",
        "setRegisterPrice",
        "symbol",
        "totalSupply",
        "transfer",
        "unclaimedGas",
        "unregisterCandidate",
        "vote",
    },
    "GasToken": {"balanceOf", "decimals", "symbol", "totalSupply", "transfer"},
    "PolicyContract": {
        "blockAccount",
        "getAttributeFee",
        "getBlockedAccounts",
        "getExecFeeFactor",
        "getExecPicoFeeFactor",
        "getFeePerByte",
        "getMaxTraceableBlocks",
        "getMaxValidUntilBlockIncrement",
        "getMillisecondsPerBlock",
        "getStoragePrice",
        "getWhitelistFeeContracts",
        "isBlocked",
        "recoverFund",
        "removeWhitelistFeeContract",
        "setAttributeFee",
        "setExecFeeFactor",
        "setFeePerByte",
        "setMaxTraceableBlocks",
        "setMaxValidUntilBlockIncrement",
        "setMillisecondsPerBlock",
        "setStoragePrice",
        "setWhitelistFeeContract",
        "unblockAccount",
    },
    "RoleManagement": {"designateAsRole", "getDesignatedByRole"},
    "OracleContract": {"finish", "getPrice", "request", "setPrice", "verify"},
    "Notary": {
        "balanceOf",
        "expirationOf",
        "getMaxNotValidBeforeDelta",
        "lockDepositUntil",
        "onNEP17Payment",
        "setMaxNotValidBeforeDelta",
        "verify",
        "withdraw",
    },
    "Treasury": {"onNEP11Payment", "onNEP17Payment", "verify"},
}

EXPECTED_NATIVE_IDS_AND_HASHES_V391: dict[str, tuple[int, str]] = {
    "ContractManagement": (-1, "0xfffdc93764dbaddd97c48f252a53ea4643faa3fd"),
    "StdLib": (-2, "0xacce6fd80d44e1796aa0c2c625e9e4e0ce39efc0"),
    "CryptoLib": (-3, "0x726cb6e0cd8628a1350a611384688911ab75f51b"),
    "LedgerContract": (-4, "0xda65b600f7124ce6c79950c1772a36403104f2be"),
    "NeoToken": (-5, "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5"),
    "GasToken": (-6, "0xd2a4cff31913016155e38e474a2c06d08be276cf"),
    "PolicyContract": (-7, "0xcc5e4edd9f5f8dba8bb65734541df7a1c081c67b"),
    "RoleManagement": (-8, "0x49cf4e5378ffcd4dec034fd98a174c5491e395e2"),
    "OracleContract": (-9, "0xfe924b7cfe89ddd271abaf7210a80a7e11178758"),
    "Notary": (-10, "0xc1e14f19c3e60d0b9244d06dd7ba9b113135ec3b"),
    "Treasury": (-11, "0x156326f25b1b5d839a4d326aeaa75383c9563ac1"),
}


EXPECTED_EVENTS_V391: dict[str, list[tuple[str, tuple[tuple[str, str], ...]]]] = {
    "ContractManagement": [
        ("Deploy", (("Hash", "Hash160"),)),
        ("Update", (("Hash", "Hash160"),)),
        ("Destroy", (("Hash", "Hash160"),)),
    ],
    "StdLib": [],
    "CryptoLib": [],
    "LedgerContract": [],
    "NeoToken": [
        ("Transfer", (("from", "Hash160"), ("to", "Hash160"), ("amount", "Integer"))),
        (
            "CandidateStateChanged",
            (("pubkey", "PublicKey"), ("registered", "Boolean"), ("votes", "Integer")),
        ),
        (
            "Vote",
            (
                ("account", "Hash160"),
                ("from", "PublicKey"),
                ("to", "PublicKey"),
                ("amount", "Integer"),
            ),
        ),
        ("CommitteeChanged", (("old", "Array"), ("new", "Array"))),
    ],
    "GasToken": [("Transfer", (("from", "Hash160"), ("to", "Hash160"), ("amount", "Integer")))],
    "PolicyContract": [
        ("MillisecondsPerBlockChanged", (("old", "Integer"), ("new", "Integer"))),
        (
            "WhitelistFeeChanged",
            (
                ("contract", "Hash160"),
                ("method", "String"),
                ("argCount", "Integer"),
                ("fee", "Any"),
            ),
        ),
        ("RecoveredFund", (("account", "Hash160"),)),
    ],
    "RoleManagement": [
        (
            "Designation",
            (("Role", "Integer"), ("BlockIndex", "Integer"), ("Old", "Array"), ("New", "Array")),
        )
    ],
    "OracleContract": [
        (
            "OracleRequest",
            (
                ("Id", "Integer"),
                ("RequestContract", "Hash160"),
                ("Url", "String"),
                ("Filter", "String"),
            ),
        ),
        ("OracleResponse", (("Id", "Integer"), ("OriginalTx", "Hash256"))),
    ],
    "Notary": [],
    "Treasury": [],
}


EXPECTED_POLICY_METHOD_FLAGS_V391: dict[str, CallFlags] = {
    "blockAccount": CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
    "getAttributeFee": CallFlags.READ_STATES,
    "getBlockedAccounts": CallFlags.READ_STATES,
    "getExecFeeFactor": CallFlags.READ_STATES,
    "getExecPicoFeeFactor": CallFlags.READ_STATES,
    "getFeePerByte": CallFlags.READ_STATES,
    "getMaxTraceableBlocks": CallFlags.READ_STATES,
    "getMaxValidUntilBlockIncrement": CallFlags.READ_STATES,
    "getMillisecondsPerBlock": CallFlags.READ_STATES,
    "getStoragePrice": CallFlags.READ_STATES,
    "getWhitelistFeeContracts": CallFlags.READ_STATES,
    "isBlocked": CallFlags.READ_STATES,
    "recoverFund": CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
    "removeWhitelistFeeContract": CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
    "setAttributeFee": CallFlags.STATES,
    "setExecFeeFactor": CallFlags.STATES,
    "setFeePerByte": CallFlags.STATES,
    "setMaxTraceableBlocks": CallFlags.STATES,
    "setMaxValidUntilBlockIncrement": CallFlags.STATES,
    "setMillisecondsPerBlock": CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
    "setStoragePrice": CallFlags.STATES,
    "setWhitelistFeeContract": CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
    "unblockAccount": CallFlags.STATES,
}


EXPECTED_CONTRACT_MANAGEMENT_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "deploy": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 0),
    "destroy": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 1 << 15),
    "getContract": (CallFlags.READ_STATES, 1 << 15),
    "getContractById": (CallFlags.READ_STATES, 1 << 15),
    "getContractHashes": (CallFlags.READ_STATES, 1 << 15),
    "getMinimumDeploymentFee": (CallFlags.READ_STATES, 1 << 15),
    "hasMethod": (CallFlags.READ_STATES, 1 << 15),
    "isContract": (CallFlags.READ_STATES, 1 << 14),
    "setMinimumDeploymentFee": (CallFlags.STATES, 1 << 15),
    "update": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 0),
}


EXPECTED_NEOTOKEN_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "balanceOf": (CallFlags.READ_STATES, 1 << 15),
    "decimals": (CallFlags.NONE, 0),
    "getAccountState": (CallFlags.READ_STATES, 1 << 15),
    "getAllCandidates": (CallFlags.READ_STATES, 1 << 22),
    "getCandidateVote": (CallFlags.READ_STATES, 1 << 15),
    "getCandidates": (CallFlags.READ_STATES, 1 << 22),
    "getCommittee": (CallFlags.READ_STATES, 1 << 16),
    "getCommitteeAddress": (CallFlags.READ_STATES, 1 << 16),
    "getGasPerBlock": (CallFlags.READ_STATES, 1 << 15),
    "getNextBlockValidators": (CallFlags.READ_STATES, 1 << 16),
    "getRegisterPrice": (CallFlags.READ_STATES, 1 << 15),
    "onNEP17Payment": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 0),
    "registerCandidate": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 0),
    "setGasPerBlock": (CallFlags.STATES, 1 << 15),
    "setRegisterPrice": (CallFlags.STATES, 1 << 15),
    "symbol": (CallFlags.NONE, 0),
    "totalSupply": (CallFlags.READ_STATES, 1 << 15),
    "transfer": (CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY, 1 << 17),
    "unclaimedGas": (CallFlags.READ_STATES, 1 << 17),
    "unregisterCandidate": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 1 << 16),
    "vote": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 1 << 16),
}


EXPECTED_GASTOKEN_METADATA_V391: dict[str, tuple[CallFlags, int, int]] = {
    "balanceOf": (CallFlags.READ_STATES, 1 << 15, 0),
    "decimals": (CallFlags.NONE, 0, 0),
    "symbol": (CallFlags.NONE, 0, 0),
    "totalSupply": (CallFlags.READ_STATES, 1 << 15, 0),
    "transfer": (CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY, 1 << 17, 50),
}


EXPECTED_STDLIB_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "atoi": (CallFlags.NONE, 1 << 6),
    "base58CheckDecode": (CallFlags.NONE, 1 << 16),
    "base58CheckEncode": (CallFlags.NONE, 1 << 16),
    "base58Decode": (CallFlags.NONE, 1 << 10),
    "base58Encode": (CallFlags.NONE, 1 << 13),
    "base64Decode": (CallFlags.NONE, 1 << 5),
    "base64Encode": (CallFlags.NONE, 1 << 5),
    "base64UrlDecode": (CallFlags.NONE, 1 << 5),
    "base64UrlEncode": (CallFlags.NONE, 1 << 5),
    "deserialize": (CallFlags.NONE, 1 << 14),
    "hexDecode": (CallFlags.NONE, 1 << 5),
    "hexEncode": (CallFlags.NONE, 1 << 5),
    "itoa": (CallFlags.NONE, 1 << 12),
    "jsonDeserialize": (CallFlags.NONE, 1 << 14),
    "jsonSerialize": (CallFlags.NONE, 1 << 12),
    "memoryCompare": (CallFlags.NONE, 1 << 5),
    "memorySearch": (CallFlags.NONE, 1 << 6),
    "serialize": (CallFlags.NONE, 1 << 12),
    "strLen": (CallFlags.NONE, 1 << 8),
    "stringSplit": (CallFlags.NONE, 1 << 8),
}


EXPECTED_CRYPTOLIB_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "bls12381Add": (CallFlags.NONE, 1 << 19),
    "bls12381Deserialize": (CallFlags.NONE, 1 << 19),
    "bls12381Equal": (CallFlags.NONE, 1 << 5),
    "bls12381Mul": (CallFlags.NONE, 1 << 21),
    "bls12381Pairing": (CallFlags.NONE, 1 << 23),
    "bls12381Serialize": (CallFlags.NONE, 1 << 19),
    "keccak256": (CallFlags.NONE, 1 << 15),
    "murmur32": (CallFlags.NONE, 1 << 13),
    "recoverSecp256K1": (CallFlags.NONE, 1 << 15),
    "ripemd160": (CallFlags.NONE, 1 << 15),
    "sha256": (CallFlags.NONE, 1 << 15),
    "verifyWithECDsa": (CallFlags.NONE, 1 << 15),
    "verifyWithEd25519": (CallFlags.NONE, 1 << 15),
}


EXPECTED_LEDGER_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "currentHash": (CallFlags.READ_STATES, 1 << 15),
    "currentIndex": (CallFlags.READ_STATES, 1 << 15),
    "getBlock": (CallFlags.READ_STATES, 1 << 15),
    "getTransaction": (CallFlags.READ_STATES, 1 << 15),
    "getTransactionFromBlock": (CallFlags.READ_STATES, 1 << 16),
    "getTransactionHeight": (CallFlags.READ_STATES, 1 << 15),
    "getTransactionSigners": (CallFlags.READ_STATES, 1 << 15),
    "getTransactionVMState": (CallFlags.READ_STATES, 1 << 15),
}


EXPECTED_ROLE_MANAGEMENT_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "designateAsRole": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 1 << 15),
    "getDesignatedByRole": (CallFlags.READ_STATES, 1 << 15),
}


EXPECTED_ORACLE_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "finish": (CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY, 0),
    "getPrice": (CallFlags.READ_STATES, 1 << 15),
    "request": (CallFlags.STATES | CallFlags.ALLOW_NOTIFY, 0),
    "setPrice": (CallFlags.STATES, 1 << 15),
    "verify": (CallFlags.NONE, 1 << 15),
}


EXPECTED_NOTARY_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "balanceOf": (CallFlags.READ_STATES, 1 << 15),
    "expirationOf": (CallFlags.READ_STATES, 1 << 15),
    "getMaxNotValidBeforeDelta": (CallFlags.READ_STATES, 1 << 15),
    "lockDepositUntil": (CallFlags.STATES, 1 << 15),
    "onNEP17Payment": (CallFlags.STATES, 1 << 15),
    "setMaxNotValidBeforeDelta": (CallFlags.STATES, 1 << 15),
    "verify": (CallFlags.READ_STATES, 1 << 15),
    "withdraw": (CallFlags.ALL, 1 << 15),
}


EXPECTED_TREASURY_METADATA_V391: dict[str, tuple[CallFlags, int]] = {
    "onNEP11Payment": (CallFlags.NONE, 1 << 5),
    "onNEP17Payment": (CallFlags.NONE, 1 << 5),
    "verify": (CallFlags.READ_STATES, 1 << 5),
}


def test_native_method_surface_matches_v391() -> None:
    contracts = initialize_native_contracts()

    assert set(contracts.keys()) == set(EXPECTED_METHODS_V391.keys())

    for name, expected in EXPECTED_METHODS_V391.items():
        actual = set(contracts[name]._methods.keys())  # noqa: SLF001 - method surface lock test
        assert actual == expected, name


def test_native_contract_ids_and_hashes_match_v391() -> None:
    contracts = initialize_native_contracts()

    assert set(contracts.keys()) == set(EXPECTED_NATIVE_IDS_AND_HASHES_V391.keys())

    for name, (expected_id, expected_hash) in EXPECTED_NATIVE_IDS_AND_HASHES_V391.items():
        contract = contracts[name]
        assert contract.id == expected_id, name
        assert str(contract.hash).lower() == expected_hash, name
        assert NativeContract.get_contract_by_id(expected_id) is contract
        assert NativeContract.get_contract_by_name(name) is contract
        assert NativeContract.get_contract(contract.hash) is contract


def test_native_event_surface_matches_v391() -> None:
    contracts = initialize_native_contracts()
    cm = contracts["ContractManagement"]

    settings = ProtocolSettings.mainnet()
    settings.hardforks[Hardfork.HF_ECHIDNA] = 100
    settings.hardforks[Hardfork.HF_COCKATRICE] = 150
    settings.hardforks[Hardfork.HF_FAUN] = 200
    snapshot = SimpleNamespace(
        get=lambda _key: None,
        protocol_settings=settings,
        persisting_block=SimpleNamespace(index=200),
    )

    for name, expected_events in EXPECTED_EVENTS_V391.items():
        state = cm.get_contract_state(snapshot, contracts[name].hash)
        assert state is not None, name
        manifest = json.loads(state.manifest.decode("utf-8"))
        actual = [
            (
                event["name"],
                tuple((param["name"], param["type"]) for param in event.get("parameters", [])),
            )
            for event in manifest["abi"]["events"]
        ]
        assert actual == expected_events, name


def test_native_method_descriptor_order_matches_v391_canonical_sort() -> None:
    contracts = initialize_native_contracts()

    for contract in contracts.values():
        ordered = sorted(
            contract._method_entries,  # noqa: SLF001 - metadata lock test
            key=lambda method: (method.name, _abi_parameter_count(method)),
        )
        expected_names = [method.name for method in ordered]
        assert contract._method_order == expected_names, contract.name  # noqa: SLF001 - metadata lock test

        for index, method in enumerate(ordered):
            expected_offset = index * 7
            assert method.descriptor.offset == expected_offset, f"{contract.name}.{method.name}"
            assert contract.get_method_by_offset(expected_offset) is method


def _abi_parameter_count(method) -> int:
    signature = inspect.signature(method.handler)
    parameters = list(signature.parameters.values())
    count = 0
    for index, parameter in enumerate(parameters):
        if index == 0 and parameter.name in {"engine", "snapshot", "context"}:
            continue
        if (
            len(parameters) == 2
            and index == 1
            and parameter.name == "context"
            and parameter.default is not inspect._empty
        ):
            continue
        count += 1
    return count


def test_policy_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]

    for method_name, expected_flags in EXPECTED_POLICY_METHOD_FLAGS_V391.items():
        metadata = policy.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == 1 << 15, method_name


def test_contract_management_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    contract_management = contracts["ContractManagement"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_CONTRACT_MANAGEMENT_METADATA_V391.items():
        metadata = contract_management.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_neo_token_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    neo_token = contracts["NeoToken"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_NEOTOKEN_METADATA_V391.items():
        metadata = neo_token.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_gas_token_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    gas_token = contracts["GasToken"]

    for method_name, (expected_flags, expected_cpu_fee, expected_storage_fee) in EXPECTED_GASTOKEN_METADATA_V391.items():
        metadata = gas_token.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name
        assert metadata.storage_fee == expected_storage_fee, method_name


def test_stdlib_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    stdlib = contracts["StdLib"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_STDLIB_METADATA_V391.items():
        metadata = stdlib.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_crypto_lib_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    crypto_lib = contracts["CryptoLib"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_CRYPTOLIB_METADATA_V391.items():
        metadata = crypto_lib.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_ledger_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    ledger = contracts["LedgerContract"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_LEDGER_METADATA_V391.items():
        metadata = ledger.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_role_management_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    role_management = contracts["RoleManagement"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_ROLE_MANAGEMENT_METADATA_V391.items():
        metadata = role_management.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_oracle_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    oracle = contracts["OracleContract"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_ORACLE_METADATA_V391.items():
        metadata = oracle.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_notary_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    notary = contracts["Notary"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_NOTARY_METADATA_V391.items():
        metadata = notary.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name


def test_treasury_method_metadata_matches_v391() -> None:
    contracts = initialize_native_contracts()
    treasury = contracts["Treasury"]

    for method_name, (expected_flags, expected_cpu_fee) in EXPECTED_TREASURY_METADATA_V391.items():
        metadata = treasury.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name
