"""Tests for ContractManagement native contract."""

from __future__ import annotations

import inspect
import json
from collections import Counter

from types import SimpleNamespace

import pytest

from neo.hardfork import Hardfork
from neo.native import initialize_native_contracts
from neo.native.contract_management import ContractManagement
from neo.protocol_settings import ProtocolSettings
from neo.types import UInt160


class TestContractManagement:
    """Tests for ContractManagement."""
    
    def test_name(self):
        """Test contract name."""
        cm = ContractManagement()
        assert cm.name == "ContractManagement"

    def test_is_contract_is_hardfork_gated_by_echidna(self):
        cm = ContractManagement()

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100

        snapshot_pre = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=99),
        )
        with pytest.raises(KeyError, match="isContract"):
            cm.is_contract(snapshot_pre, UInt160.ZERO)

        snapshot_post = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=100),
        )
        assert cm.is_contract(snapshot_post, UInt160.ZERO) is False

    def test_is_contract_without_block_context_defaults_to_height_zero(self):
        cm = ContractManagement()

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100

        # No persisting_block available: hardfork activation check should
        # evaluate at block height 0 and keep Echidna-gated methods inactive.
        snapshot = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
        )

        with pytest.raises(KeyError, match="isContract"):
            cm.is_contract(snapshot, UInt160.ZERO)

    def test_get_contract_state_returns_generated_native_state(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        policy = contracts["PolicyContract"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_FAUN] = 200

        snapshot_pre_faun = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=199),
        )
        native_state_pre = cm.get_contract_state(snapshot_pre_faun, policy.hash)
        assert native_state_pre is not None
        assert native_state_pre.id == policy.id
        assert native_state_pre.hash == policy.hash

        manifest_pre = json.loads(native_state_pre.manifest.decode("utf-8"))
        methods_pre = {m["name"]: m for m in manifest_pre["abi"]["methods"]}
        assert "getExecPicoFeeFactor" not in methods_pre
        assert methods_pre["getStoragePrice"]["offset"] == 49
        assert len(native_state_pre.nef) == len(methods_pre) * 7

        snapshot_post_faun = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=200),
        )
        native_state_post = cm.get_contract_state(snapshot_post_faun, policy.hash)
        assert native_state_post is not None
        manifest_post = json.loads(native_state_post.manifest.decode("utf-8"))
        methods_post = {m["name"]: m for m in manifest_post["abi"]["methods"]}
        assert methods_post["getExecPicoFeeFactor"]["offset"] == 28

    def test_get_contract_state_by_id_returns_native_state_for_negative_id(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        stdlib = contracts["StdLib"]

        snapshot = SimpleNamespace(get=lambda _key: None)
        native_state = cm.get_contract_state_by_id(snapshot, stdlib.id)
        assert native_state is not None
        assert native_state.id == stdlib.id
        assert native_state.hash == stdlib.hash

    def test_native_contract_activation_follows_hardforks(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        notary = contracts["Notary"]
        treasury = contracts["Treasury"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_FAUN] = 200

        snapshot_pre_echidna = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=99),
        )
        snapshot_post_echidna = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=100),
        )
        snapshot_pre_faun = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=199),
        )
        snapshot_post_faun = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=200),
        )

        assert cm.get_contract_state(snapshot_pre_echidna, notary.hash) is None
        assert cm.get_contract_state(snapshot_post_echidna, notary.hash) is not None
        assert cm.get_contract_state(snapshot_pre_faun, treasury.hash) is None
        assert cm.get_contract_state(snapshot_post_faun, treasury.hash) is not None
        assert cm.get_contract_state_by_id(snapshot_pre_echidna, notary.id) is None
        assert cm.get_contract_state_by_id(snapshot_post_echidna, notary.id) is not None
        assert cm.get_contract_state_by_id(snapshot_pre_faun, treasury.id) is None
        assert cm.get_contract_state_by_id(snapshot_post_faun, treasury.id) is not None

        assert cm.is_contract(snapshot_post_echidna, notary.hash) is True
        assert cm.is_contract(snapshot_post_echidna, treasury.hash) is False
        assert cm.is_contract(snapshot_post_faun, treasury.hash) is True

    def test_native_update_counter_follows_hardfork_reinitialization(self):
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

        expected_update_counter = {
            "ContractManagement": 1,
            "StdLib": 2,
            "CryptoLib": 2,
            "LedgerContract": 0,
            "NeoToken": 2,
            "GasToken": 0,
            "PolicyContract": 2,
            "RoleManagement": 1,
            "OracleContract": 1,
            "Notary": 1,
            "Treasury": 0,
        }

        for name, expected in expected_update_counter.items():
            contract = contracts[name]
            state = cm.get_contract_state(snapshot, contract.hash)
            assert state is not None, name
            assert state.update_counter == expected, name

    def test_crypto_lib_method_activation_follows_hardforks(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        crypto = contracts["CryptoLib"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_COCKATRICE] = 150

        def _snapshot(index: int):
            return SimpleNamespace(
                get=lambda _key: None,
                protocol_settings=settings,
                persisting_block=SimpleNamespace(index=index),
            )

        snapshot_pre_echidna = _snapshot(99)
        state_pre_echidna = cm.get_contract_state(snapshot_pre_echidna, crypto.hash)
        assert state_pre_echidna is not None
        methods_pre_echidna = json.loads(state_pre_echidna.manifest.decode("utf-8"))["abi"]["methods"]
        names_pre_echidna = [method["name"] for method in methods_pre_echidna]
        assert "verifyWithECDsa" in names_pre_echidna
        assert names_pre_echidna.count("verifyWithECDsa") == 1
        assert "verifyWithEd25519" not in names_pre_echidna
        assert "recoverSecp256K1" not in names_pre_echidna
        assert "keccak256" not in names_pre_echidna

        snapshot_pre_cockatrice = _snapshot(149)
        state_pre_cockatrice = cm.get_contract_state(snapshot_pre_cockatrice, crypto.hash)
        assert state_pre_cockatrice is not None
        names_pre_cockatrice = [
            method["name"]
            for method in json.loads(state_pre_cockatrice.manifest.decode("utf-8"))["abi"]["methods"]
        ]
        assert names_pre_cockatrice.count("verifyWithECDsa") == 1
        assert "verifyWithEd25519" in names_pre_cockatrice
        assert "recoverSecp256K1" in names_pre_cockatrice
        assert "keccak256" not in names_pre_cockatrice

        snapshot_post_cockatrice = _snapshot(150)
        state_post_cockatrice = cm.get_contract_state(snapshot_post_cockatrice, crypto.hash)
        assert state_post_cockatrice is not None
        names_post_cockatrice = [
            method["name"]
            for method in json.loads(state_post_cockatrice.manifest.decode("utf-8"))["abi"]["methods"]
        ]
        assert names_post_cockatrice.count("verifyWithECDsa") == 1
        assert "verifyWithEd25519" in names_post_cockatrice
        assert "recoverSecp256K1" in names_post_cockatrice
        assert "keccak256" in names_post_cockatrice

        verify_pre_cockatrice = crypto.get_method_if_active(
            "verifyWithECDsa", snapshot_pre_cockatrice
        )
        verify_post_cockatrice = crypto.get_method_if_active(
            "verifyWithECDsa", snapshot_post_cockatrice
        )
        assert verify_pre_cockatrice is not None
        assert verify_post_cockatrice is not None
        assert verify_pre_cockatrice.deprecated_in == Hardfork.HF_COCKATRICE
        assert verify_pre_cockatrice.active_in is None
        assert verify_post_cockatrice.active_in == Hardfork.HF_COCKATRICE
        assert verify_post_cockatrice.deprecated_in is None

    def test_get_contract_state_manifest_supported_standards_follow_hardforks(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        neo_token = contracts["NeoToken"]
        oracle = contracts["OracleContract"]
        notary = contracts["Notary"]
        treasury = contracts["Treasury"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_FAUN] = 200

        snapshot_pre_echidna = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=99),
        )
        neo_pre = cm.get_contract_state(snapshot_pre_echidna, neo_token.hash)
        assert neo_pre is not None
        manifest_neo_pre = json.loads(neo_pre.manifest.decode("utf-8"))
        assert manifest_neo_pre["supportedstandards"] == ["NEP-17"]

        snapshot_post_echidna = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=100),
        )
        neo_post = cm.get_contract_state(snapshot_post_echidna, neo_token.hash)
        assert neo_post is not None
        manifest_neo_post = json.loads(neo_post.manifest.decode("utf-8"))
        assert manifest_neo_post["supportedstandards"] == ["NEP-17", "NEP-27"]

        snapshot_pre_faun = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=199),
        )
        oracle_pre = cm.get_contract_state(snapshot_pre_faun, oracle.hash)
        notary_pre = cm.get_contract_state(snapshot_pre_faun, notary.hash)
        assert oracle_pre is not None
        assert notary_pre is not None
        assert cm.get_contract_state(snapshot_pre_faun, treasury.hash) is None
        manifest_oracle_pre = json.loads(oracle_pre.manifest.decode("utf-8"))
        manifest_notary_pre = json.loads(notary_pre.manifest.decode("utf-8"))
        assert manifest_oracle_pre["supportedstandards"] == []
        assert manifest_notary_pre["supportedstandards"] == ["NEP-27"]

        snapshot_post_faun = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=200),
        )
        oracle_post = cm.get_contract_state(snapshot_post_faun, oracle.hash)
        notary_post = cm.get_contract_state(snapshot_post_faun, notary.hash)
        treasury_post = cm.get_contract_state(snapshot_post_faun, treasury.hash)
        assert oracle_post is not None
        assert notary_post is not None
        assert treasury_post is not None
        manifest_oracle_post = json.loads(oracle_post.manifest.decode("utf-8"))
        manifest_notary_post = json.loads(notary_post.manifest.decode("utf-8"))
        manifest_treasury_post = json.loads(treasury_post.manifest.decode("utf-8"))
        assert manifest_oracle_post["supportedstandards"] == ["NEP-30"]
        assert manifest_notary_post["supportedstandards"] == ["NEP-27", "NEP-30"]
        assert manifest_treasury_post["supportedstandards"] == ["NEP-26", "NEP-27", "NEP-30"]

    def test_has_method_uses_generated_native_manifest_abi(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        gas = contracts["GasToken"]

        snapshot = SimpleNamespace(get=lambda _key: None)
        assert cm.has_method(snapshot, gas.hash, "symbol", 0) is True
        assert cm.has_method(snapshot, gas.hash, "balanceOf", 1) is True
        assert cm.has_method(snapshot, gas.hash, "transfer", 4) is True
        assert cm.has_method(snapshot, gas.hash, "transfer", 3) is False

    def test_generated_native_manifest_matches_active_callnative_surface(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_FAUN] = 200

        for index in (99, 100, 199, 200):
            snapshot = SimpleNamespace(
                get=lambda _key: None,
                protocol_settings=settings,
                persisting_block=SimpleNamespace(index=index),
            )
            for contract in contracts.values():
                state = cm.get_contract_state(snapshot, contract.hash)
                if not contract.is_contract_active(snapshot):
                    assert state is None
                    continue
                assert state is not None
                manifest = json.loads(state.manifest.decode("utf-8"))
                methods = manifest["abi"]["methods"]

                active_by_offset = contract.get_active_methods_by_offset(snapshot)
                expected_names = [metadata.name for _, metadata in sorted(active_by_offset.items())]
                assert [method["name"] for method in methods] == expected_names
                assert [method["offset"] for method in methods] == list(range(0, len(methods) * 7, 7))
                assert len(state.nef) == len(methods) * 7

                expected_counts = Counter(
                    (metadata.name, _abi_parameter_count(metadata.handler))
                    for metadata in active_by_offset.values()
                )
                actual_counts = Counter(
                    (method["name"], len(method["parameters"])) for method in methods
                )
                assert actual_counts == expected_counts

    def test_generated_native_manifest_events_follow_hardforks(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        neo = contracts["NeoToken"]
        role = contracts["RoleManagement"]
        policy = contracts["PolicyContract"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_COCKATRICE] = 150
        settings.hardforks[Hardfork.HF_FAUN] = 200

        snapshot_pre_echidna = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=99),
        )
        role_pre = cm.get_contract_state(snapshot_pre_echidna, role.hash)
        policy_pre = cm.get_contract_state(snapshot_pre_echidna, policy.hash)
        assert role_pre is not None
        assert policy_pre is not None
        role_pre_events = json.loads(role_pre.manifest.decode("utf-8"))["abi"]["events"]
        policy_pre_events = json.loads(policy_pre.manifest.decode("utf-8"))["abi"]["events"]
        assert role_pre_events[0]["name"] == "Designation"
        assert len(role_pre_events[0]["parameters"]) == 2
        assert policy_pre_events == []

        snapshot_post_echidna = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=100),
        )
        role_post_e = cm.get_contract_state(snapshot_post_echidna, role.hash)
        policy_post_e = cm.get_contract_state(snapshot_post_echidna, policy.hash)
        assert role_post_e is not None
        assert policy_post_e is not None
        role_post_e_events = json.loads(role_post_e.manifest.decode("utf-8"))["abi"]["events"]
        policy_post_e_events = json.loads(policy_post_e.manifest.decode("utf-8"))["abi"]["events"]
        assert len(role_post_e_events[0]["parameters"]) == 4
        assert [event["name"] for event in policy_post_e_events] == ["MillisecondsPerBlockChanged"]

        snapshot_pre_cockatrice = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=149),
        )
        neo_pre_c = cm.get_contract_state(snapshot_pre_cockatrice, neo.hash)
        assert neo_pre_c is not None
        neo_pre_c_events = json.loads(neo_pre_c.manifest.decode("utf-8"))["abi"]["events"]
        assert [event["name"] for event in neo_pre_c_events] == [
            "Transfer",
            "CandidateStateChanged",
            "Vote",
        ]

        snapshot_post_cockatrice = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=150),
        )
        neo_post_c = cm.get_contract_state(snapshot_post_cockatrice, neo.hash)
        assert neo_post_c is not None
        neo_post_c_events = json.loads(neo_post_c.manifest.decode("utf-8"))["abi"]["events"]
        assert [event["name"] for event in neo_post_c_events] == [
            "Transfer",
            "CandidateStateChanged",
            "Vote",
            "CommitteeChanged",
        ]

        snapshot_post_faun = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=200),
        )
        policy_post_f = cm.get_contract_state(snapshot_post_faun, policy.hash)
        assert policy_post_f is not None
        policy_post_f_events = json.loads(policy_post_f.manifest.decode("utf-8"))["abi"]["events"]
        assert [event["name"] for event in policy_post_f_events] == [
            "MillisecondsPerBlockChanged",
            "WhitelistFeeChanged",
            "RecoveredFund",
        ]

    def test_generated_stdlib_manifest_abi_types_match_v391(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        stdlib = contracts["StdLib"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_FAUN] = 200
        snapshot = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=200),
        )

        state = cm.get_contract_state(snapshot, stdlib.hash)
        assert state is not None
        manifest = json.loads(state.manifest.decode("utf-8"))
        methods = {method["name"]: method for method in manifest["abi"]["methods"]}
        abi_methods = manifest["abi"]["methods"]

        assert methods["base64UrlEncode"]["parameters"] == [{"name": "data", "type": "String"}]
        assert methods["base64UrlEncode"]["returntype"] == "String"

        assert methods["base64UrlDecode"]["parameters"] == [{"name": "s", "type": "String"}]
        assert methods["base64UrlDecode"]["returntype"] == "String"

        assert methods["hexEncode"]["parameters"] == [{"name": "bytes", "type": "ByteArray"}]
        assert methods["hexEncode"]["returntype"] == "String"

        assert methods["hexDecode"]["parameters"] == [{"name": "str", "type": "String"}]
        assert methods["hexDecode"]["returntype"] == "ByteArray"

        assert sorted(
            (
                tuple(parameter["type"] for parameter in method["parameters"]),
                method["returntype"],
            )
            for method in abi_methods
            if method["name"] == "itoa"
        ) == [
            (("Integer",), "String"),
            (("Integer", "Integer"), "String"),
        ]
        assert sorted(
            (
                tuple(parameter["type"] for parameter in method["parameters"]),
                method["returntype"],
            )
            for method in abi_methods
            if method["name"] == "atoi"
        ) == [
            (("String",), "Integer"),
            (("String", "Integer"), "Integer"),
        ]
        assert sorted(
            (
                tuple(parameter["type"] for parameter in method["parameters"]),
                method["returntype"],
            )
            for method in abi_methods
            if method["name"] == "memorySearch"
        ) == [
            (("ByteArray", "ByteArray"), "Integer"),
            (("ByteArray", "ByteArray", "Integer"), "Integer"),
            (("ByteArray", "ByteArray", "Integer", "Boolean"), "Integer"),
        ]
        assert sorted(
            (
                tuple(parameter["type"] for parameter in method["parameters"]),
                method["returntype"],
            )
            for method in abi_methods
            if method["name"] == "stringSplit"
        ) == [
            (("String", "String"), "Array"),
            (("String", "String", "Boolean"), "Array"),
        ]

    def test_generated_core_native_manifest_abi_types_match_v391(self):
        contracts = initialize_native_contracts()
        cm = contracts["ContractManagement"]
        crypto = contracts["CryptoLib"]
        ledger = contracts["LedgerContract"]
        neo = contracts["NeoToken"]
        policy = contracts["PolicyContract"]
        role = contracts["RoleManagement"]
        treasury = contracts["Treasury"]

        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_FAUN] = 200
        snapshot = SimpleNamespace(
            get=lambda _key: None,
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=200),
        )

        cm_state = cm.get_contract_state(snapshot, cm.hash)
        assert cm_state is not None
        cm_manifest = json.loads(cm_state.manifest.decode("utf-8"))
        cm_methods = {method["name"]: method for method in cm_manifest["abi"]["methods"]}
        cm_abi_methods = cm_manifest["abi"]["methods"]
        assert cm_methods["getContract"]["returntype"] == "Array"
        assert cm_methods["getContractById"]["returntype"] == "Array"
        assert cm_methods["getContractHashes"]["returntype"] == "InteropInterface"
        assert sorted(
            (
                tuple(parameter["type"] for parameter in method["parameters"]),
                method["returntype"],
            )
            for method in cm_abi_methods
            if method["name"] == "deploy"
        ) == [
            (("ByteArray", "ByteArray"), "Array"),
            (("ByteArray", "ByteArray", "Any"), "Array"),
        ]
        assert sorted(
            (
                tuple(parameter["type"] for parameter in method["parameters"]),
                method["returntype"],
            )
            for method in cm_abi_methods
            if method["name"] == "update"
        ) == [
            (("ByteArray", "ByteArray"), "Void"),
            (("ByteArray", "ByteArray", "Any"), "Void"),
        ]

        crypto_state = cm.get_contract_state(snapshot, crypto.hash)
        assert crypto_state is not None
        crypto_manifest = json.loads(crypto_state.manifest.decode("utf-8"))
        crypto_methods = {method["name"]: method for method in crypto_manifest["abi"]["methods"]}
        assert crypto_methods["bls12381Add"]["parameters"] == [
            {"name": "x", "type": "InteropInterface"},
            {"name": "y", "type": "InteropInterface"},
        ]
        assert crypto_methods["bls12381Add"]["returntype"] == "InteropInterface"
        assert crypto_methods["bls12381Deserialize"]["parameters"] == [
            {"name": "data", "type": "ByteArray"}
        ]
        assert crypto_methods["bls12381Deserialize"]["returntype"] == "InteropInterface"
        assert crypto_methods["bls12381Equal"]["parameters"] == [
            {"name": "x", "type": "InteropInterface"},
            {"name": "y", "type": "InteropInterface"},
        ]
        assert crypto_methods["bls12381Equal"]["returntype"] == "Boolean"
        assert crypto_methods["bls12381Mul"]["parameters"] == [
            {"name": "x", "type": "InteropInterface"},
            {"name": "mul", "type": "ByteArray"},
            {"name": "neg", "type": "Boolean"},
        ]
        assert crypto_methods["bls12381Mul"]["returntype"] == "InteropInterface"
        assert crypto_methods["bls12381Pairing"]["parameters"] == [
            {"name": "g1", "type": "InteropInterface"},
            {"name": "g2", "type": "InteropInterface"},
        ]
        assert crypto_methods["bls12381Pairing"]["returntype"] == "InteropInterface"
        assert crypto_methods["bls12381Serialize"]["parameters"] == [
            {"name": "g", "type": "InteropInterface"}
        ]
        assert crypto_methods["bls12381Serialize"]["returntype"] == "ByteArray"

        ledger_state = cm.get_contract_state(snapshot, ledger.hash)
        assert ledger_state is not None
        ledger_manifest = json.loads(ledger_state.manifest.decode("utf-8"))
        ledger_methods = {method["name"]: method for method in ledger_manifest["abi"]["methods"]}
        assert ledger_methods["getBlock"]["parameters"] == [
            {"name": "indexOrHash", "type": "ByteArray"}
        ]
        assert ledger_methods["getBlock"]["returntype"] == "Array"
        assert ledger_methods["getTransaction"]["parameters"] == [
            {"name": "hash", "type": "Hash256"}
        ]
        assert ledger_methods["getTransaction"]["returntype"] == "Array"
        assert ledger_methods["getTransactionFromBlock"]["parameters"] == [
            {"name": "blockIndexOrHash", "type": "ByteArray"},
            {"name": "txIndex", "type": "Integer"},
        ]
        assert ledger_methods["getTransactionFromBlock"]["returntype"] == "Array"
        assert ledger_methods["getTransactionSigners"]["returntype"] == "Array"
        assert ledger_methods["getTransactionVMState"]["returntype"] == "Integer"

        policy_state = cm.get_contract_state(snapshot, policy.hash)
        assert policy_state is not None
        policy_manifest = json.loads(policy_state.manifest.decode("utf-8"))
        policy_methods = {method["name"]: method for method in policy_manifest["abi"]["methods"]}
        assert policy_methods["getBlockedAccounts"]["returntype"] == "InteropInterface"
        assert policy_methods["getWhitelistFeeContracts"]["returntype"] == "InteropInterface"

        neo_state = cm.get_contract_state(snapshot, neo.hash)
        assert neo_state is not None
        neo_manifest = json.loads(neo_state.manifest.decode("utf-8"))
        neo_methods = {method["name"]: method for method in neo_manifest["abi"]["methods"]}
        assert neo_methods["getAllCandidates"]["returntype"] == "InteropInterface"
        assert neo_methods["getCandidateVote"]["parameters"] == [
            {"name": "pubKey", "type": "PublicKey"}
        ]
        assert neo_methods["getCandidateVote"]["returntype"] == "Integer"
        assert neo_methods["registerCandidate"]["parameters"] == [
            {"name": "pubkey", "type": "PublicKey"}
        ]
        assert neo_methods["registerCandidate"]["returntype"] == "Boolean"
        assert neo_methods["unregisterCandidate"]["parameters"] == [
            {"name": "pubkey", "type": "PublicKey"}
        ]
        assert neo_methods["unregisterCandidate"]["returntype"] == "Boolean"
        assert neo_methods["vote"]["parameters"] == [
            {"name": "account", "type": "Hash160"},
            {"name": "voteTo", "type": "PublicKey"},
        ]
        assert neo_methods["vote"]["returntype"] == "Boolean"

        treasury_state = cm.get_contract_state(snapshot, treasury.hash)
        assert treasury_state is not None
        treasury_manifest = json.loads(treasury_state.manifest.decode("utf-8"))
        treasury_methods = {method["name"]: method for method in treasury_manifest["abi"]["methods"]}
        assert treasury_methods["onNEP11Payment"]["parameters"] == [
            {"name": "from", "type": "Hash160"},
            {"name": "amount", "type": "Integer"},
            {"name": "tokenId", "type": "ByteArray"},
            {"name": "data", "type": "Any"},
        ]
        assert treasury_methods["onNEP11Payment"]["returntype"] == "Void"
        assert treasury_methods["onNEP17Payment"]["parameters"] == [
            {"name": "from", "type": "Hash160"},
            {"name": "amount", "type": "Integer"},
            {"name": "data", "type": "Any"},
        ]
        assert treasury_methods["onNEP17Payment"]["returntype"] == "Void"

        role_state = cm.get_contract_state(snapshot, role.hash)
        assert role_state is not None
        role_manifest = json.loads(role_state.manifest.decode("utf-8"))
        role_methods = {method["name"]: method for method in role_manifest["abi"]["methods"]}
        assert role_methods["designateAsRole"]["parameters"] == [
            {"name": "role", "type": "Integer"},
            {"name": "nodes", "type": "Array"},
        ]
        assert role_methods["getDesignatedByRole"]["returntype"] == "Array"


def _abi_parameter_count(handler) -> int:
    signature = inspect.signature(handler)
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
