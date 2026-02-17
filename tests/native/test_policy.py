"""Tests for Policy native contract."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from neo.hardfork import Hardfork
from neo.native.contract_management import ContractManagement, ContractState, PREFIX_CONTRACT
from neo.native.native_contract import StorageItem
from neo.native.neo_token import CandidateState, PREFIX_CANDIDATE
from neo.native.policy import (
    PolicyContract,
    DEFAULT_EXEC_FEE_FACTOR,
    DEFAULT_STORAGE_PRICE,
    DEFAULT_FEE_PER_BYTE,
    MAX_MAX_TRACEABLE_BLOCKS,
    MAX_MAX_VALID_UNTIL_BLOCK_INCREMENT,
    MAX_MILLISECONDS_PER_BLOCK,
    MAX_EXEC_FEE_FACTOR,
    MAX_STORAGE_PRICE,
    PREFIX_BLOCKED_ACCOUNT,
    PREFIX_MAX_TRACEABLE_BLOCKS,
    PREFIX_MAX_VALID_UNTIL_BLOCK_INCREMENT,
    PREFIX_WHITELIST_FEE,
)
from neo.native import initialize_native_contracts
from neo.protocol_settings import ProtocolSettings
from neo.types import UInt160


class _Snapshot:
    def __init__(self) -> None:
        self._data: dict[Any, StorageItem] = {}

    def get(self, key: Any) -> StorageItem | None:
        return self._data.get(key)

    def add(self, key: Any, item: StorageItem) -> None:
        self._data[key] = item

    def contains(self, key: Any) -> bool:
        return key in self._data

    def delete(self, key: Any) -> None:
        self._data.pop(key, None)

    def get_and_change(self, key: Any, factory=None) -> StorageItem:
        item = self._data.get(key)
        if item is None:
            item = factory() if factory is not None else StorageItem()
            self._data[key] = item
        return item


class _Engine:
    def __init__(
        self,
        committee: bool = True,
        almost_committee: bool = True,
        now_ms: int = 0,
        witness: bool = True,
    ) -> None:
        self.snapshot = _Snapshot()
        self._committee = committee
        self._almost_committee = almost_committee
        self._now_ms = now_ms
        self._witness = witness
        self.notifications: list[tuple[Any, str, list[Any]]] = []
        self.calling_script_hash = UInt160.ZERO

    def check_committee(self) -> bool:
        return self._committee

    def check_almost_committee(self) -> bool:
        return self._almost_committee

    def get_time(self) -> int:
        return self._now_ms

    def send_notification(self, contract_hash: Any, event_name: str, state: list[Any]) -> None:
        self.notifications.append((contract_hash, event_name, state))

    def is_contract(self, _account: UInt160) -> bool:
        return False

    def call_contract(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def check_witness(self, _account: UInt160) -> bool:
        return self._witness


def _add_contract_state(
    snapshot: _Snapshot,
    contract_management: ContractManagement,
    contract_hash: UInt160,
    method_name: str,
    arg_count: int,
    offset: int,
) -> None:
    method = {
        "name": method_name,
        "parameters": [{"name": f"arg{i}", "type": "Any"} for i in range(arg_count)],
        "offset": offset,
    }
    manifest = {"abi": {"methods": [method]}}
    state = ContractState(
        id=1,
        update_counter=0,
        hash=contract_hash,
        nef=b"\x01",
        manifest=json.dumps(manifest).encode("utf-8"),
    )
    key = contract_management._create_storage_key(PREFIX_CONTRACT, contract_hash.data)  # noqa: SLF001
    snapshot.add(key, StorageItem(state.to_bytes()))


def _fresh_native_contracts() -> dict[str, Any]:
    return initialize_native_contracts()


def _engine_with_hardfork_index(
    *,
    index: int,
    committee: bool = True,
    almost_committee: bool = True,
    now_ms: int = 0,
    witness: bool = True,
) -> _Engine:
    settings = ProtocolSettings.mainnet()
    settings.hardforks[Hardfork.HF_ECHIDNA] = 100
    settings.hardforks[Hardfork.HF_FAUN] = 200

    engine = _Engine(
        committee=committee,
        almost_committee=almost_committee,
        now_ms=now_ms,
        witness=witness,
    )
    engine.protocol_settings = settings
    engine.snapshot.protocol_settings = settings
    engine.snapshot.persisting_block = SimpleNamespace(index=index)
    return engine


class TestPolicyContract:
    """Tests for PolicyContract."""
    
    def test_name(self):
        """Test contract name."""
        policy = PolicyContract()
        assert policy.name == "PolicyContract"
    
    def test_default_constants(self):
        """Test default constant values."""
        assert DEFAULT_EXEC_FEE_FACTOR == 1
        assert DEFAULT_STORAGE_PRICE == 1000
        assert DEFAULT_FEE_PER_BYTE == 20
    
    def test_max_constants(self):
        """Test maximum constant values."""
        assert MAX_EXEC_FEE_FACTOR == 100
        assert MAX_STORAGE_PRICE == 10000000
        assert MAX_MILLISECONDS_PER_BLOCK == 30_000
        assert MAX_MAX_VALID_UNTIL_BLOCK_INCREMENT == 86_400
        assert MAX_MAX_TRACEABLE_BLOCKS == 2_102_400
        assert PREFIX_WHITELIST_FEE == 16

    def test_v391_additional_read_defaults(self):
        """Additional v3.9.1 read-method defaults."""
        policy = PolicyContract()

        class _Snap:
            def get(self, _key):
                return None

        snap = _Snap()
        assert policy.get_exec_pico_fee_factor(snap) == 10000
        assert policy.get_milliseconds_per_block(snap) == 15000
        assert policy.get_max_valid_until_block_increment(snap) == 5760
        assert policy.get_max_traceable_blocks(snap) == 2_102_400

    def test_set_max_valid_until_block_increment_checks_traceable_ceiling(self) -> None:
        policy = PolicyContract()
        engine = _Engine(committee=True)

        trace_key = policy._create_storage_key(PREFIX_MAX_TRACEABLE_BLOCKS)  # noqa: SLF001
        trace_item = StorageItem()
        trace_item.set(8_000)
        engine.snapshot.add(trace_key, trace_item)

        with pytest.raises(ValueError, match="lower than MaxTraceableBlocks"):
            policy.set_max_valid_until_block_increment(engine, 8_000)

    def test_setters_enforce_v391_upper_bounds(self) -> None:
        policy = PolicyContract()
        engine = _Engine(committee=True)

        with pytest.raises(ValueError, match=r"MillisecondsPerBlock must be between \[1, 30000\]"):
            policy.set_milliseconds_per_block(engine, 30_001)

        with pytest.raises(
            ValueError,
            match=r"MaxValidUntilBlockIncrement must be between \[1, 86400\]",
        ):
            policy.set_max_valid_until_block_increment(engine, 86_401)

        with pytest.raises(
            ValueError,
            match=r"MaxTraceableBlocks must be between \[1, 2102400\]",
        ):
            policy.set_max_traceable_blocks(engine, 2_102_401)

    def test_echidna_setters_are_not_active_before_echidna(self) -> None:
        policy = PolicyContract()
        engine = _engine_with_hardfork_index(index=99, committee=True)

        with pytest.raises(KeyError, match="setMillisecondsPerBlock"):
            policy.set_milliseconds_per_block(engine, 15_000)

        with pytest.raises(KeyError, match="setMaxValidUntilBlockIncrement"):
            policy.set_max_valid_until_block_increment(engine, 5_000)

        with pytest.raises(KeyError, match="setMaxTraceableBlocks"):
            policy.set_max_traceable_blocks(engine, 6_000)

    def test_echidna_getters_are_not_active_before_echidna(self) -> None:
        policy = PolicyContract()
        engine = _engine_with_hardfork_index(index=99, committee=True)

        with pytest.raises(KeyError, match="getMillisecondsPerBlock"):
            policy.get_milliseconds_per_block(engine.snapshot)

        with pytest.raises(KeyError, match="getMaxValidUntilBlockIncrement"):
            policy.get_max_valid_until_block_increment(engine.snapshot)

        with pytest.raises(KeyError, match="getMaxTraceableBlocks"):
            policy.get_max_traceable_blocks(engine.snapshot)

    def test_get_exec_pico_fee_factor_is_not_active_before_faun(self) -> None:
        policy = PolicyContract()
        pre_faun = _engine_with_hardfork_index(index=199)
        at_faun = _engine_with_hardfork_index(index=200)

        with pytest.raises(KeyError, match="getExecPicoFeeFactor"):
            policy.get_exec_pico_fee_factor(pre_faun.snapshot)

        assert policy.get_exec_pico_fee_factor(at_faun.snapshot) == 10000

    def test_set_max_traceable_blocks_cannot_increase(self) -> None:
        policy = PolicyContract()
        engine = _Engine(committee=True)

        trace_key = policy._create_storage_key(PREFIX_MAX_TRACEABLE_BLOCKS)  # noqa: SLF001
        trace_item = StorageItem()
        trace_item.set(10_000)
        engine.snapshot.add(trace_key, trace_item)

        max_vub_key = policy._create_storage_key(PREFIX_MAX_VALID_UNTIL_BLOCK_INCREMENT)  # noqa: SLF001
        max_vub_item = StorageItem()
        max_vub_item.set(1_000)
        engine.snapshot.add(max_vub_key, max_vub_item)

        with pytest.raises(ValueError, match="can not be increased"):
            policy.set_max_traceable_blocks(engine, 12_000)

    def test_set_max_traceable_blocks_must_exceed_max_valid_until(self) -> None:
        policy = PolicyContract()
        engine = _Engine(committee=True)

        trace_key = policy._create_storage_key(PREFIX_MAX_TRACEABLE_BLOCKS)  # noqa: SLF001
        trace_item = StorageItem()
        trace_item.set(10_000)
        engine.snapshot.add(trace_key, trace_item)

        max_vub_key = policy._create_storage_key(PREFIX_MAX_VALID_UNTIL_BLOCK_INCREMENT)  # noqa: SLF001
        max_vub_item = StorageItem()
        max_vub_item.set(9_000)
        engine.snapshot.add(max_vub_key, max_vub_item)

        with pytest.raises(ValueError, match="larger than MaxValidUntilBlockIncrement"):
            policy.set_max_traceable_blocks(engine, 9_000)

    def test_set_whitelist_fee_contract_uses_method_offset_key(self) -> None:
        contract_management = ContractManagement()
        policy = PolicyContract()
        engine = _Engine(committee=True)

        target_hash = UInt160(b"\x12" * 20)
        _add_contract_state(
            snapshot=engine.snapshot,
            contract_management=contract_management,
            contract_hash=target_hash,
            method_name="balanceOf",
            arg_count=1,
            offset=42,
        )

        policy.set_whitelist_fee_contract(engine, target_hash, "balanceOf", 1, 777)

        expected_key = policy._create_storage_key(PREFIX_WHITELIST_FEE, target_hash.data, 42)  # noqa: SLF001
        stored = engine.snapshot.get(expected_key)
        assert stored is not None
        assert int(stored) == 777

    def test_set_whitelist_fee_contract_rejects_unknown_contract_or_method(self) -> None:
        contract_management = ContractManagement()
        policy = PolicyContract()
        engine = _Engine(committee=True)

        unknown_hash = UInt160(b"\x21" * 20)
        with pytest.raises(ValueError, match="Is not a valid contract"):
            policy.set_whitelist_fee_contract(engine, unknown_hash, "balanceOf", 1, 10)

        known_hash = UInt160(b"\x34" * 20)
        _add_contract_state(
            snapshot=engine.snapshot,
            contract_management=contract_management,
            contract_hash=known_hash,
            method_name="transfer",
            arg_count=3,
            offset=21,
        )
        with pytest.raises(ValueError, match="Method balanceOf with 1 args was not found"):
            policy.set_whitelist_fee_contract(engine, known_hash, "balanceOf", 1, 10)

    def test_remove_whitelist_fee_contract_requires_existing_entry(self) -> None:
        contract_management = ContractManagement()
        policy = PolicyContract()
        engine = _Engine(committee=True)

        target_hash = UInt160(b"\x56" * 20)
        _add_contract_state(
            snapshot=engine.snapshot,
            contract_management=contract_management,
            contract_hash=target_hash,
            method_name="vote",
            arg_count=2,
            offset=99,
        )

        with pytest.raises(ValueError, match="Whitelist not found"):
            policy.remove_whitelist_fee_contract(engine, target_hash, "vote", 2)

        policy.set_whitelist_fee_contract(engine, target_hash, "vote", 2, 99_000)
        key = policy._create_storage_key(PREFIX_WHITELIST_FEE, target_hash.data, 99)  # noqa: SLF001
        assert engine.snapshot.contains(key)

        policy.remove_whitelist_fee_contract(engine, target_hash, "vote", 2)
        assert not engine.snapshot.contains(key)

    def test_faun_methods_are_not_active_before_faun(self) -> None:
        policy = PolicyContract()
        engine = _engine_with_hardfork_index(index=199, committee=True, almost_committee=True)
        any_hash = UInt160(b"\x61" * 20)

        with pytest.raises(KeyError, match="setWhitelistFeeContract"):
            policy.set_whitelist_fee_contract(engine, any_hash, "balanceOf", 1, 10)

        with pytest.raises(KeyError, match="removeWhitelistFeeContract"):
            policy.remove_whitelist_fee_contract(engine, any_hash, "balanceOf", 1)

        with pytest.raises(KeyError, match="recoverFund"):
            policy.recover_fund(engine, any_hash, any_hash)

    def test_faun_iterators_are_not_active_before_faun(self) -> None:
        policy = PolicyContract()
        pre_faun = _engine_with_hardfork_index(index=199)
        at_faun = _engine_with_hardfork_index(index=200)

        with pytest.raises(KeyError, match="getBlockedAccounts"):
            list(policy.get_blocked_accounts(pre_faun.snapshot))

        with pytest.raises(KeyError, match="getWhitelistFeeContracts"):
            list(policy.get_whitelist_fee_contracts(pre_faun.snapshot))

        assert list(policy.get_blocked_accounts(at_faun.snapshot)) == []
        assert list(policy.get_whitelist_fee_contracts(at_faun.snapshot)) == []

    def test_block_account_before_faun_keeps_vote_and_stores_empty_item(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        neo = contracts["NeoToken"]

        engine = _engine_with_hardfork_index(index=199, committee=True, now_ms=987_654)
        account = UInt160(b"\x62" * 20)
        candidate = b"\x02" + b"\x33" * 32

        candidate_key = neo._create_storage_key(PREFIX_CANDIDATE, candidate)  # noqa: SLF001
        engine.snapshot.add(candidate_key, StorageItem(CandidateState(registered=True, votes=0).to_bytes()))

        neo.mint(engine, account, 80)
        assert neo.vote(engine, account, candidate) is True

        assert policy.block_account(engine, account) is True
        assert neo.get_account_state(engine.snapshot, account).vote_to == candidate
        assert neo.get_candidate_vote(engine.snapshot, candidate) == 80

        blocked_key = policy._create_storage_key(PREFIX_BLOCKED_ACCOUNT, account.data)  # noqa: SLF001
        blocked_item = engine.snapshot.get(blocked_key)
        assert blocked_item is not None
        assert blocked_item.value == b""

    def test_block_account_at_faun_clears_vote_and_stores_timestamp(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        neo = contracts["NeoToken"]

        engine = _engine_with_hardfork_index(index=200, committee=True, now_ms=123_456)
        account = UInt160(b"\x63" * 20)
        candidate = b"\x02" + b"\x44" * 32

        candidate_key = neo._create_storage_key(PREFIX_CANDIDATE, candidate)  # noqa: SLF001
        engine.snapshot.add(candidate_key, StorageItem(CandidateState(registered=True, votes=0).to_bytes()))

        neo.mint(engine, account, 75)
        assert neo.vote(engine, account, candidate) is True

        assert policy.block_account(engine, account) is True
        assert neo.get_account_state(engine.snapshot, account).vote_to is None
        assert neo.get_candidate_vote(engine.snapshot, candidate) == 0

        blocked_key = policy._create_storage_key(PREFIX_BLOCKED_ACCOUNT, account.data)  # noqa: SLF001
        blocked_item = engine.snapshot.get(blocked_key)
        assert blocked_item is not None
        assert int(blocked_item) == 123_456

    def test_recover_fund_requires_pending_block_request(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        gas = contracts["GasToken"]

        engine = _Engine(committee=True, almost_committee=True, now_ms=0)
        blocked = UInt160(b"\x70" * 20)

        gas.mint(engine, blocked, 10)
        with pytest.raises(ValueError, match="Request not found"):
            policy.recover_fund(engine, blocked, gas.hash)

    def test_recover_fund_enforces_one_year_wait(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        gas = contracts["GasToken"]

        one_year_ms = 365 * 24 * 60 * 60 * 1000
        blocked = UInt160(b"\x71" * 20)
        engine = _Engine(committee=True, almost_committee=True, now_ms=0)

        assert policy.block_account(engine, blocked) is True
        gas.mint(engine, blocked, 10)

        engine._now_ms = one_year_ms - 1  # noqa: SLF001
        with pytest.raises(ValueError, match="at least 1 year ago"):
            policy.recover_fund(engine, blocked, gas.hash)

    def test_recover_fund_transfers_nep17_balance_to_treasury(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        gas = contracts["GasToken"]
        treasury = contracts["Treasury"]

        blocked = UInt160(b"\x72" * 20)
        one_year_ms = 365 * 24 * 60 * 60 * 1000
        engine = _Engine(committee=True, almost_committee=True, now_ms=0)

        assert policy.block_account(engine, blocked) is True
        gas.mint(engine, blocked, 250)

        assert gas.balance_of(engine.snapshot, blocked) == 250
        assert gas.balance_of(engine.snapshot, treasury.hash) == 0

        engine._now_ms = one_year_ms + 1  # noqa: SLF001
        recovered = policy.recover_fund(engine, blocked, gas.hash)

        assert recovered is True
        assert gas.balance_of(engine.snapshot, blocked) == 0
        assert gas.balance_of(engine.snapshot, treasury.hash) == 250
        assert any(event == "RecoveredFund" for _, event, _ in engine.notifications)

    def test_recover_fund_rejects_non_nep17_contract(self) -> None:
        contracts = _fresh_native_contracts()
        contract_management = contracts["ContractManagement"]
        policy: PolicyContract = contracts["PolicyContract"]

        engine = _Engine(committee=True, almost_committee=True, now_ms=0)
        blocked = UInt160(b"\x73" * 20)
        token_hash = UInt160(b"\x74" * 20)

        manifest = {
            "name": "NotNep17Token",
            "supportedstandards": ["NEP-11"],
            "abi": {"methods": []},
        }
        state = ContractState(
            id=333,
            update_counter=0,
            hash=token_hash,
            nef=b"\x01",
            manifest=json.dumps(manifest).encode("utf-8"),
        )
        key = contract_management._create_storage_key(PREFIX_CONTRACT, token_hash.data)  # noqa: SLF001
        engine.snapshot.add(key, StorageItem(state.to_bytes()))
        assert policy.block_account(engine, blocked) is True

        engine._now_ms = 365 * 24 * 60 * 60 * 1000 + 1  # noqa: SLF001
        with pytest.raises(ValueError, match="does not implement NEP-17"):
            policy.recover_fund(engine, blocked, token_hash)

    def test_block_account_clears_existing_neo_vote(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        neo = contracts["NeoToken"]

        engine = _Engine(committee=True, almost_committee=True, now_ms=0)
        account = UInt160(b"\x75" * 20)
        candidate = b"\x02" + b"\x11" * 32

        candidate_key = neo._create_storage_key(PREFIX_CANDIDATE, candidate)  # noqa: SLF001
        engine.snapshot.add(candidate_key, StorageItem(CandidateState(registered=True, votes=0).to_bytes()))

        neo.mint(engine, account, 100)
        assert neo.vote(engine, account, candidate) is True
        assert neo.get_account_state(engine.snapshot, account).vote_to == candidate
        assert neo.get_candidate_vote(engine.snapshot, candidate) == 100

        assert policy.block_account(engine, account) is True
        assert neo.get_account_state(engine.snapshot, account).vote_to is None
        assert neo.get_candidate_vote(engine.snapshot, candidate) == 0

    def test_block_account_unvotes_without_account_witness(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        neo = contracts["NeoToken"]

        engine = _Engine(committee=True, almost_committee=True, now_ms=0, witness=True)
        account = UInt160(b"\x76" * 20)
        candidate = b"\x02" + b"\x22" * 32

        candidate_key = neo._create_storage_key(PREFIX_CANDIDATE, candidate)  # noqa: SLF001
        engine.snapshot.add(candidate_key, StorageItem(CandidateState(registered=True, votes=0).to_bytes()))

        neo.mint(engine, account, 50)
        assert neo.vote(engine, account, candidate) is True
        engine._witness = False  # noqa: SLF001

        assert policy.block_account(engine, account) is True
        assert neo.get_account_state(engine.snapshot, account).vote_to is None
        assert neo.get_candidate_vote(engine.snapshot, candidate) == 0

    def test_recover_fund_supports_deployed_nep17_via_call_contract(self) -> None:
        contracts = _fresh_native_contracts()
        contract_management = contracts["ContractManagement"]
        policy: PolicyContract = contracts["PolicyContract"]
        treasury = contracts["Treasury"]

        engine = _Engine(committee=True, almost_committee=True, now_ms=0)
        blocked = UInt160(b"\x77" * 20)
        token_hash = UInt160(b"\x78" * 20)

        manifest = {
            "name": "ExternalNep17",
            "supportedstandards": ["NEP-17"],
            "abi": {
                "methods": [
                    {
                        "name": "balanceOf",
                        "parameters": [{"name": "account", "type": "Hash160"}],
                        "offset": 0,
                    },
                    {
                        "name": "transfer",
                        "parameters": [
                            {"name": "from", "type": "Hash160"},
                            {"name": "to", "type": "Hash160"},
                            {"name": "amount", "type": "Integer"},
                            {"name": "data", "type": "Any"},
                        ],
                        "offset": 7,
                    },
                ]
            },
        }
        state = ContractState(
            id=444,
            update_counter=0,
            hash=token_hash,
            nef=b"\x01",
            manifest=json.dumps(manifest).encode("utf-8"),
        )
        key = contract_management._create_storage_key(PREFIX_CONTRACT, token_hash.data)  # noqa: SLF001
        engine.snapshot.add(key, StorageItem(state.to_bytes()))

        assert policy.block_account(engine, blocked) is True
        engine._now_ms = 365 * 24 * 60 * 60 * 1000 + 1  # noqa: SLF001

        calls: list[tuple[UInt160, str, list[Any]]] = []

        def _call_contract(hash_: UInt160, method: str, args: list[Any]) -> Any:
            calls.append((hash_, method, args))
            if method == "balanceOf":
                return 123
            if method == "transfer":
                return True
            raise AssertionError(f"unexpected method {method}")

        engine.call_contract = _call_contract  # type: ignore[method-assign]

        assert policy.recover_fund(engine, blocked, token_hash) is True
        assert [name for _, name, _ in calls] == ["balanceOf", "transfer"]
        assert calls[1][2][0] == blocked
        assert calls[1][2][1] == treasury.hash
        assert calls[1][2][2] == 123

    def test_recover_fund_rejects_failed_transfer_from_deployed_nep17(self) -> None:
        contracts = _fresh_native_contracts()
        contract_management = contracts["ContractManagement"]
        policy: PolicyContract = contracts["PolicyContract"]
        treasury = contracts["Treasury"]

        engine = _Engine(committee=True, almost_committee=True, now_ms=0)
        blocked = UInt160(b"\x7a" * 20)
        token_hash = UInt160(b"\x7b" * 20)

        manifest = {
            "name": "ExternalNep17",
            "supportedstandards": ["NEP-17"],
            "abi": {
                "methods": [
                    {
                        "name": "balanceOf",
                        "parameters": [{"name": "account", "type": "Hash160"}],
                        "offset": 0,
                    },
                    {
                        "name": "transfer",
                        "parameters": [
                            {"name": "from", "type": "Hash160"},
                            {"name": "to", "type": "Hash160"},
                            {"name": "amount", "type": "Integer"},
                            {"name": "data", "type": "Any"},
                        ],
                        "offset": 7,
                    },
                ]
            },
        }
        state = ContractState(
            id=445,
            update_counter=0,
            hash=token_hash,
            nef=b"\x01",
            manifest=json.dumps(manifest).encode("utf-8"),
        )
        key = contract_management._create_storage_key(PREFIX_CONTRACT, token_hash.data)  # noqa: SLF001
        engine.snapshot.add(key, StorageItem(state.to_bytes()))

        assert policy.block_account(engine, blocked) is True
        engine._now_ms = 365 * 24 * 60 * 60 * 1000 + 1  # noqa: SLF001

        def _call_contract(hash_: UInt160, method: str, args: list[Any]) -> Any:
            if method == "balanceOf":
                return 321
            if method == "transfer":
                assert args[0] == blocked
                assert args[1] == treasury.hash
                assert args[2] == 321
                return False
            raise AssertionError(f"unexpected method {method} on {hash_}")

        engine.call_contract = _call_contract  # type: ignore[method-assign]

        with pytest.raises(ValueError, match=r"Transfer of 321 .* failed in contract"):
            policy.recover_fund(engine, blocked, token_hash)

    def test_recover_fund_native_transfer_does_not_require_account_witness(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        gas = contracts["GasToken"]
        treasury = contracts["Treasury"]

        blocked = UInt160(b"\x79" * 20)
        engine = _Engine(committee=True, almost_committee=True, now_ms=0, witness=False)

        assert policy.block_account(engine, blocked) is True
        gas.mint(engine, blocked, 90)
        engine._now_ms = 365 * 24 * 60 * 60 * 1000 + 1  # noqa: SLF001

        assert policy.recover_fund(engine, blocked, gas.hash) is True
        assert gas.balance_of(engine.snapshot, blocked) == 0
        assert gas.balance_of(engine.snapshot, treasury.hash) == 90

    def test_recover_fund_requires_almost_full_committee(self) -> None:
        contracts = _fresh_native_contracts()
        policy: PolicyContract = contracts["PolicyContract"]
        gas = contracts["GasToken"]

        blocked = UInt160(b"\x80" * 20)
        engine = _Engine(committee=True, almost_committee=True, now_ms=0)

        assert policy.block_account(engine, blocked) is True
        gas.mint(engine, blocked, 15)
        engine._now_ms = 365 * 24 * 60 * 60 * 1000 + 1  # noqa: SLF001
        engine._almost_committee = False  # noqa: SLF001

        with pytest.raises(PermissionError, match="Almost full committee"):
            policy.recover_fund(engine, blocked, gas.hash)
