"""NEO Token native contract."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from neo.crypto import hash160
from neo.crypto.ecc.point import ECPoint
from neo.hardfork import Hardfork
from neo.native.fungible_token import PREFIX_ACCOUNT, AccountState, FungibleToken
from neo.native.native_contract import CallFlags, NativeContract, StorageItem
from neo.types import UInt160

# NEO initial supply: 100 million NEO
INITIAL_SUPPLY = 100_000_000

# Storage prefixes
PREFIX_VOTERS_COUNT = 1
PREFIX_CANDIDATE = 33
PREFIX_COMMITTEE = 14
PREFIX_GAS_PER_BLOCK = 29
PREFIX_REGISTER_PRICE = 13
PREFIX_VOTER_REWARD_PER_COMMITTEE = 23

# Reward ratios
NEO_HOLDER_REWARD_RATIO = 10
COMMITTEE_REWARD_RATIO = 10
VOTER_REWARD_RATIO = 80

# Effective voter turnout threshold
EFFECTIVE_VOTER_TURNOUT = 0.2

# Vote factor for precision
VOTE_FACTOR = 100_000_000

@dataclass
class NeoAccountState(AccountState):
    """Account state for NEO token with voting support."""

    balance_height: int = 0
    vote_to: bytes | None = None  # ECPoint encoded
    last_gas_per_vote: int = 0

    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        data = self.balance.to_bytes(32, "little", signed=True)
        data += self.balance_height.to_bytes(4, "little")
        if self.vote_to:
            data += bytes([len(self.vote_to)]) + self.vote_to
        else:
            data += bytes([0])
        data += self.last_gas_per_vote.to_bytes(32, "little", signed=True)
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> NeoAccountState:
        """Deserialize from bytes."""
        state = cls()
        if not data:
            return state
        state.balance = int.from_bytes(data[:32], "little", signed=True)
        if len(data) > 32:
            state.balance_height = int.from_bytes(data[32:36], "little")
        if len(data) > 36:
            vote_len = data[36]
            if vote_len > 0:
                state.vote_to = data[37 : 37 + vote_len]
            offset = 37 + vote_len
            if len(data) > offset:
                state.last_gas_per_vote = int.from_bytes(
                    data[offset : offset + 32], "little", signed=True
                )
        return state

@dataclass
class CandidateState:
    """State for a candidate."""

    registered: bool = False
    votes: int = 0

    def to_bytes(self) -> bytes:
        data = bytes([1 if self.registered else 0])
        data += self.votes.to_bytes(32, "little", signed=True)
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> CandidateState:
        state = cls()
        if data:
            state.registered = data[0] == 1
            if len(data) > 1:
                state.votes = int.from_bytes(data[1:33], "little", signed=True)
        return state

class NeoToken(FungibleToken):
    """NEO token - governance token for the Neo blockchain."""

    TOTAL_AMOUNT = 100_000_000

    def __init__(self) -> None:
        self._total_amount = self.TOTAL_AMOUNT
        super().__init__()

    @property
    def name(self) -> str:
        return "NeoToken"

    def _contract_activations(self) -> tuple[Any | None, ...]:
        return (None, Hardfork.HF_ECHIDNA)

    @property
    def symbol(self) -> str:
        return "NEO"

    @property
    def decimals(self) -> int:
        return 0

    @property
    def total_amount(self) -> int:
        return self._total_amount

    @property
    def initial_supply(self) -> int:
        """NEO has a fixed initial supply of 100 million."""
        return self.TOTAL_AMOUNT

    def total_supply(self, snapshot: Any = None) -> int:  # type: ignore[override]
        """Total supply of NEO.

        NEO has a fixed total supply, so this remains constant regardless of snapshot.
        """
        return self.initial_supply

    def _register_methods(self) -> None:
        """Register NEO-specific methods."""
        super()._register_methods()
        self._register_method(
            "unclaimedGas", self.unclaimed_gas, cpu_fee=1 << 17, call_flags=CallFlags.READ_STATES
        )
        self._register_method(
            "getGasPerBlock",
            self.get_gas_per_block,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
        )
        self._register_method(
            "setGasPerBlock",
            self.set_gas_per_block,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES,
            manifest_parameter_names=["gasPerBlock"],
        )
        self._register_method(
            "getRegisterPrice",
            self.get_register_price,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
        )
        self._register_method(
            "setRegisterPrice",
            self.set_register_price,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES,
            manifest_parameter_names=["registerPrice"],
        )
        self._register_method(
            "registerCandidate", self.register_candidate, call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY
        )
        self._register_method(
            "unregisterCandidate",
            self.unregister_candidate,
            cpu_fee=1 << 16,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
        )
        self._register_method(
            "vote",
            self.vote,
            cpu_fee=1 << 16,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            manifest_parameter_names=["account", "voteTo"],
        )
        self._register_method(
            "getCandidates", self.get_candidates, cpu_fee=1 << 22, call_flags=CallFlags.READ_STATES
        )
        self._register_method(
            "getAllCandidates",
            self.get_all_candidates,
            cpu_fee=1 << 22,
            call_flags=CallFlags.READ_STATES,
        )
        self._register_method(
            "getCandidateVote",
            self.get_candidate_vote,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
            manifest_parameter_names=["pubKey"],
        )
        self._register_method(
            "getCommittee", self.get_committee, cpu_fee=1 << 16, call_flags=CallFlags.READ_STATES
        )
        self._register_method(
            "getCommitteeAddress",
            self.get_committee_address,
            cpu_fee=1 << 16,
            call_flags=CallFlags.READ_STATES,
        )
        self._register_method(
            "getNextBlockValidators",
            self.get_next_block_validators,
            cpu_fee=1 << 16,
            call_flags=CallFlags.READ_STATES,
        )
        self._register_method(
            "getAccountState",
            self.get_account_state,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
        )
        self._register_method(
            "onNEP17Payment",
            self.on_nep17_payment,
            cpu_fee=0,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            manifest_parameter_names=["from", "amount", "data"],
        )

    def _register_events(self) -> None:
        """Register NEO-specific events."""
        super()._register_events()
        self._register_event(
            "CandidateStateChanged",
            [("pubkey", "PublicKey"), ("registered", "Boolean"), ("votes", "Integer")],
            order=1,
        )
        self._register_event(
            "Vote",
            [
                ("account", "Hash160"),
                ("from", "PublicKey"),
                ("to", "PublicKey"),
                ("amount", "Integer"),
            ],
            order=2,
        )
        self._register_event(
            "CommitteeChanged",
            [("old", "Array"), ("new", "Array")],
            order=3,
            active_in=Hardfork.HF_COCKATRICE,
        )

    def _native_supported_standards(self, context: Any) -> list[str]:
        standards = ["NEP-17"]
        settings, _ = self._hardfork_context(context)
        if settings is not None and self.is_hardfork_enabled(context, Hardfork.HF_ECHIDNA):
            standards.append("NEP-27")
        return standards

    def _get_account_state(self, item: StorageItem) -> NeoAccountState:
        """Get NEO account state from storage item."""
        return NeoAccountState.from_bytes(item.value)

    def _on_balance_changing(
        self, engine: Any, account: UInt160, state: NeoAccountState, amount: int
    ) -> None:
        """Mirror C# OnBalanceChanging (NeoToken.cs:87-102).

        Queues the accrued GAS distribution for the account and, when the
        account is currently voting and its balance changes, keeps the global
        voters count and the candidate's vote tally in sync.
        """
        distribution = self._distribute_gas(engine, account, state)
        if distribution is not None:
            self._queue_gas_distribution(engine, distribution)
        if amount == 0:
            return
        if state.vote_to is None:
            return
        voters_key = self._create_storage_key(PREFIX_VOTERS_COUNT)
        voters_item = engine.snapshot.get_and_change(voters_key, lambda: StorageItem())
        voters_item.add(amount)
        cand_key = self._create_storage_key(PREFIX_CANDIDATE, state.vote_to)
        cand_item = engine.snapshot.get_and_change(cand_key)
        if cand_item is not None:
            candidate = CandidateState.from_bytes(cand_item.value)
            candidate.votes += amount
            cand_item.value = candidate.to_bytes()
            self._check_candidate(engine.snapshot, state.vote_to, candidate)

    @staticmethod
    def _queue_gas_distribution(engine: Any, distribution: tuple[UInt160, int]) -> None:
        """Queue a GAS distribution to be minted after the transfer completes.

        C# stores the pending distributions on the current execution context
        and drains them in PostTransferAsync; the spec lacks that context state
        machinery, so the queue is kept on the engine instead.
        """
        queue = getattr(engine, "_neo_gas_distributions", None)
        if queue is None:
            queue = []
            try:
                engine._neo_gas_distributions = queue
            except (AttributeError, TypeError):
                return
        queue.append(distribution)

    def _post_transfer(
        self,
        engine: Any,
        from_account: UInt160 | None,
        to_account: UInt160 | None,
        amount: int,
        data: Any,
        call_on_payment: bool,
    ) -> None:
        """Mirror C# PostTransferAsync (NeoToken.cs:104-110): emit the Transfer
        notification / onNEP17Payment, then mint every queued GAS distribution.
        """
        super()._post_transfer(engine, from_account, to_account, amount, data, call_on_payment)
        queue = getattr(engine, "_neo_gas_distributions", None)
        if not queue:
            return
        # Drain so a single transfer's distributions are minted exactly once.
        engine._neo_gas_distributions = []
        for dist_account, dist_amount in queue:
            self._mint_gas(engine, dist_account, dist_amount, call_on_payment)

    def _create_account_state(self) -> NeoAccountState:
        """Create a new NEO account state."""
        return NeoAccountState()

    def _sorted_gas_records(self, snapshot: Any, end: int) -> list[tuple[int, int]]:
        """Return (index, gasPerBlock) records with index <= end, descending.

        Mirrors C# GetSortedGasRecords (NeoToken.cs:325-331): seeks the
        Prefix_GasPerBlock records backward from `end`. The block index is the
        4-byte suffix of the storage key; we decode it (the spec stores it as a
        little-endian uint32 via StorageKey.create) and sort descending so the
        first element is the record effective at `end`.
        """
        prefix = self._create_storage_key(PREFIX_GAS_PER_BLOCK)
        records: list[tuple[int, int]] = []
        if hasattr(snapshot, "find"):
            for key, item in snapshot.find(prefix):
                suffix = key.key[1:]  # strip the prefix byte
                if len(suffix) < 4:
                    continue
                index = int.from_bytes(suffix[:4], "little")
                if index <= end:
                    records.append((index, int(item)))
        records.sort(key=lambda r: r[0], reverse=True)
        return records

    def get_gas_per_block(self, snapshot: Any) -> int:
        """Get the current GAS generated per block.

        Mirrors C# GetGasPerBlock (NeoToken.cs:309-312): returns the
        gasPerBlock of the record effective at CurrentIndex+1 (the highest
        index <= CurrentIndex+1).
        """
        end = self._current_index(snapshot) + 1
        records = self._sorted_gas_records(snapshot, end)
        if records:
            return records[0][1]
        return 5 * 10**8  # Default 5 GAS

    def set_gas_per_block(self, engine: Any, gas_per_block: int) -> None:
        """Set GAS per block. Committee only."""
        if gas_per_block < 0 or gas_per_block > 10 * 10**8:
            raise ValueError("GasPerBlock out of range")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")

        index = engine.persisting_block.index + 1
        key = self._create_storage_key(PREFIX_GAS_PER_BLOCK, index)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(gas_per_block)

    def get_register_price(self, snapshot: Any) -> int:
        """Get the price to register as a candidate."""
        key = self._create_storage_key(PREFIX_REGISTER_PRICE)
        item = snapshot.get(key)
        return int(item) if item else 1000 * 10**8  # Default 1000 GAS

    def set_register_price(self, engine: Any, price: int) -> None:
        """Set register price. Committee only."""
        if price <= 0:
            raise ValueError("RegisterPrice must be positive")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")

        key = self._create_storage_key(PREFIX_REGISTER_PRICE)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.set(price)

    def unclaimed_gas(self, engine: Any, account: UInt160, end: int) -> int:
        """Get unclaimed GAS for an account."""
        # Mirror C# NeoToken.UnclaimedGas (NeoToken.cs:357-365): the requested
        # end must equal the expected end (persisting block index, or current
        # ledger index + 1 when no block is persisting). Otherwise FAULT.
        expect_end = self._expected_end(engine)
        if end != expect_end:
            raise ValueError(
                f"end ({end}) does not equal the expected end ({expect_end})"
            )
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = engine.snapshot.get(key)
        if item is None:
            return 0
        state = self._get_account_state(item)
        return self._calculate_bonus(engine.snapshot, state, end)

    @staticmethod
    def _current_index(snapshot: Any) -> int:
        """Return the current ledger block index (Ledger.CurrentIndex)."""
        ledger = NativeContract.get_contract_by_name("LedgerContract")
        if ledger is None:
            return 0
        return ledger.current_index(snapshot)

    def _expected_end(self, engine: Any) -> int:
        """Mirror C# expectEnd = PersistingBlock?.Index ?? CurrentIndex + 1."""
        block = getattr(engine, "persisting_block", None)
        if block is not None:
            return block.index
        return self._current_index(engine.snapshot) + 1

    def _calculate_bonus(self, snapshot: Any, state: NeoAccountState, end: int) -> int:
        """Calculate GAS bonus for holding NEO."""
        if state.balance == 0:
            return 0
        if state.balance < 0:
            raise ValueError("Balance cannot be negative")
        if state.balance_height >= end:
            return 0

        # Calculate NEO holder reward.
        # Mirror C# CalculateReward (NeoToken.cs:155-180): sum gasPerBlock over
        # each window between historical GasPerBlock records, scanning backward
        # from end-1, so multiple rate changes are accounted for.
        start = state.balance_height
        cur_end = end
        sum_gas_per_block = 0
        for index, gas_per_block_i in self._sorted_gas_records(snapshot, end - 1):
            if index > start:
                sum_gas_per_block += gas_per_block_i * (cur_end - index)
                cur_end = index
            else:
                sum_gas_per_block += gas_per_block_i * (cur_end - start)
                break
        neo_holder_reward = (
            state.balance
            * sum_gas_per_block
            * NEO_HOLDER_REWARD_RATIO
            // 100
            // self._total_amount
        )

        # Calculate vote reward if voting
        vote_reward = 0
        if state.vote_to is not None:
            key = self._create_storage_key(PREFIX_VOTER_REWARD_PER_COMMITTEE, state.vote_to)
            item = snapshot.get(key)
            if item:
                latest_gas_per_vote = int(item)
                vote_reward = (
                    state.balance * (latest_gas_per_vote - state.last_gas_per_vote) // VOTE_FACTOR
                )

        return neo_holder_reward + vote_reward

    @staticmethod
    def _pubkey_bytes(pubkey: ECPoint | bytes | None) -> bytes | None:
        if pubkey is None:
            return None
        if isinstance(pubkey, bytes):
            return pubkey
        encoder = getattr(pubkey, "encode", None)
        if callable(encoder):
            try:
                encoded = encoder(compressed=True)
            except TypeError:
                encoded = encoder()
            if isinstance(encoded, (bytes, bytearray, memoryview)):
                return bytes(encoded)
        raw_data = getattr(pubkey, "data", None)
        if isinstance(raw_data, (bytes, bytearray, memoryview)):
            return bytes(raw_data)
        bytes_method = getattr(pubkey, "__bytes__", None)
        if callable(bytes_method):
            converted = bytes_method()
            if isinstance(converted, (bytes, bytearray, memoryview)):
                return bytes(converted)
        return None

    def register_candidate(self, engine: Any, pubkey: ECPoint) -> bool:
        """Register as a candidate.

        Mirrors C# RegisterCandidate (NeoToken.cs:391-409): charges the
        register price fee then delegates to register_internal.
        """
        pubkey_bytes = self._pubkey_bytes(pubkey)
        if pubkey_bytes is None:
            return False
        if not engine.check_witness_pubkey(pubkey_bytes):
            return False

        # Charge registration fee
        engine.add_fee(self.get_register_price(engine.snapshot))

        return self.register_internal(engine, pubkey_bytes)

    def register_internal(self, engine: Any, pubkey_bytes: bytes) -> bool:
        """Mirror C# RegisterInternal (NeoToken.cs:411-423).

        Performs the witness check, creates/updates the CandidateState and
        emits the CandidateStateChanged notification; does NOT charge a fee.
        """
        if not engine.check_witness_pubkey(pubkey_bytes):
            return False

        key = self._create_storage_key(PREFIX_CANDIDATE, pubkey_bytes)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem(CandidateState().to_bytes()))
        state = CandidateState.from_bytes(item.value)

        if state.registered:
            return True

        state.registered = True
        item.value = state.to_bytes()

        engine.send_notification(self.hash, "CandidateStateChanged", [pubkey_bytes, True, state.votes])
        return True

    def unregister_candidate(self, engine: Any, pubkey: ECPoint) -> bool:
        """Unregister as a candidate."""
        pubkey_bytes = self._pubkey_bytes(pubkey)
        if pubkey_bytes is None:
            return False
        if not engine.check_witness_pubkey(pubkey_bytes):
            return False

        key = self._create_storage_key(PREFIX_CANDIDATE, pubkey_bytes)
        item = engine.snapshot.get(key)
        if item is None:
            return True

        item = engine.snapshot.get_and_change(key)
        state = CandidateState.from_bytes(item.value)
        if not state.registered:
            return True

        state.registered = False
        item.value = state.to_bytes()
        self._check_candidate(engine.snapshot, pubkey_bytes, state)

        engine.send_notification(self.hash, "CandidateStateChanged", [pubkey_bytes, False, state.votes])
        return True

    def _check_candidate(self, snapshot: Any, pubkey: bytes, candidate: CandidateState) -> None:
        """Remove candidate if unregistered and has no votes."""
        if not candidate.registered and candidate.votes == 0:
            key = self._create_storage_key(PREFIX_CANDIDATE, pubkey)
            snapshot.delete(key)
            reward_key = self._create_storage_key(PREFIX_VOTER_REWARD_PER_COMMITTEE, pubkey)
            snapshot.delete(reward_key)

    def vote(self, engine: Any, account: UInt160, vote_to: ECPoint | None) -> bool:
        """Vote for a candidate."""
        if not engine.check_witness(account):
            return False
        return self.vote_internal(engine, account, vote_to)

    def _voter_reward_per_committee(self, snapshot: Any, pubkey: bytes) -> int:
        """Return the cumulative VoterRewardPerCommittee for a candidate (0 default)."""
        key = self._create_storage_key(PREFIX_VOTER_REWARD_PER_COMMITTEE, pubkey)
        item = snapshot.get(key)
        return int(item) if item else 0

    def _distribute_gas(
        self, engine: Any, account: UInt160, state: NeoAccountState
    ) -> tuple[UInt160, int] | None:
        """Mirror C# DistributeGas (NeoToken.cs:124-144).

        Computes the GAS bonus owed to the account, advances the account's
        balance_height to the persisting block, and refreshes last_gas_per_vote
        from the account's current vote target. Returns (account, amount) when
        non-zero, else None.
        """
        block = getattr(engine, "persisting_block", None)
        if block is None:
            block = getattr(getattr(engine, "snapshot", None), "persisting_block", None)
        # PersistingBlock is null when running under the debugger.
        if block is None:
            return None
        datoshi = self._calculate_bonus(engine.snapshot, state, block.index)
        state.balance_height = block.index
        if state.vote_to is not None:
            state.last_gas_per_vote = self._voter_reward_per_committee(
                engine.snapshot, state.vote_to
            )
        if datoshi == 0:
            return None
        return (account, datoshi)

    def vote_internal(self, engine: Any, account: UInt160, vote_to: ECPoint | None) -> bool:
        """Internal vote update that skips witness checks.

        Mirrors C# VoteInternal (NeoToken.cs:464-516).
        """
        vote_to_bytes = self._pubkey_bytes(vote_to)
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = engine.snapshot.get_and_change(key)
        if item is None:
            return False

        state = self._get_account_state(item)
        if state.balance == 0:
            return False

        # Validate new candidate
        if vote_to_bytes is not None:
            cand_key = self._create_storage_key(PREFIX_CANDIDATE, vote_to_bytes)
            cand_item = engine.snapshot.get_and_change(cand_key)
            if cand_item is None:
                return False
            new_cand = CandidateState.from_bytes(cand_item.value)
            if not new_cand.registered:
                return False
        else:
            cand_item = None
            new_cand = None

        # Update voters count (XOR of old/new vote presence)
        voters_key = self._create_storage_key(PREFIX_VOTERS_COUNT)
        if (state.vote_to is None) != (vote_to_bytes is None):
            voters_item = engine.snapshot.get_and_change(voters_key, lambda: StorageItem())
            if state.vote_to is None:
                voters_item.add(state.balance)
            else:
                voters_item.add(-state.balance)

        # Distribute accrued GAS BEFORE mutating votes (NeoToken.cs:485).
        gas_distribution = self._distribute_gas(engine, account, state)

        # Remove votes from old candidate
        old_vote = state.vote_to
        if state.vote_to is not None:
            old_key = self._create_storage_key(PREFIX_CANDIDATE, state.vote_to)
            old_item = engine.snapshot.get_and_change(old_key)
            if old_item:
                old_cand = CandidateState.from_bytes(old_item.value)
                old_cand.votes -= state.balance
                old_item.value = old_cand.to_bytes()
                self._check_candidate(engine.snapshot, state.vote_to, old_cand)

        # last_gas_per_vote: latest reward of new target when switching to a
        # different candidate (NeoToken.cs:494-498).
        if vote_to_bytes is not None and vote_to_bytes != old_vote:
            state.last_gas_per_vote = self._voter_reward_per_committee(
                engine.snapshot, vote_to_bytes
            )

        # Add votes to new candidate; else clear last_gas_per_vote
        state.vote_to = vote_to_bytes
        if new_cand is not None and cand_item is not None:
            new_cand.votes += state.balance
            cand_item.value = new_cand.to_bytes()
        else:
            state.last_gas_per_vote = 0

        item.value = state.to_bytes()
        engine.send_notification(self.hash, "Vote", [account, old_vote, vote_to_bytes, state.balance])

        # Mint the distributed GAS to the account (NeoToken.cs:513-514).
        if gas_distribution is not None:
            self._mint_gas(engine, gas_distribution[0], gas_distribution[1], True)
        return True

    @staticmethod
    def _mint_gas(engine: Any, account: UInt160, amount: int, call_on_payment: bool) -> None:
        """Mint GAS to an account via the GAS native contract, if available."""
        if amount == 0:
            return
        gas = NativeContract.get_contract_by_name("GasToken")
        if gas is None:
            return
        gas.mint(engine, account, amount, call_on_payment)

    def get_candidates(self, snapshot: Any) -> list[tuple[bytes, int]]:
        """Get all registered candidates with their votes."""
        candidates = []
        prefix = self._create_storage_key(PREFIX_CANDIDATE)
        for key, item in snapshot.find(prefix):
            state = CandidateState.from_bytes(item.value)
            if not state.registered:
                continue
            pubkey = key.key[1:]  # Remove prefix
            # Mirror C# GetCandidatesInternal (NeoToken.cs:553): exclude any
            # candidate whose signature-redeem-script account is blocked by the
            # Policy contract.
            if self._is_candidate_blocked(snapshot, pubkey):
                continue
            candidates.append((pubkey, state.votes))
        return candidates[:256]  # Max 256 candidates

    @staticmethod
    def _is_candidate_blocked(snapshot: Any, pubkey: bytes) -> bool:
        """Return True if the candidate's account hash is blocked by Policy.

        The account is the ToScriptHash of the single-key signature redeem
        script of the public key (NOT the raw pubkey bytes), matching C#
        Contract.CreateSignatureRedeemScript(pubkey).ToScriptHash().
        """
        policy = NativeContract.get_contract_by_name("PolicyContract")
        if policy is None:
            return False
        from neo.smartcontract.syscalls.contract import (
            _create_signature_redeem_script,
        )

        script = _create_signature_redeem_script(pubkey)
        account_hash = UInt160(hash160(script))
        return policy.is_blocked(snapshot, account_hash)

    def get_all_candidates(self, snapshot: Any) -> Iterator[tuple[bytes, int]]:
        """Get an iterator over registered candidates and votes."""
        return iter(self.get_candidates(snapshot))

    def get_candidate_vote(self, snapshot: Any, pubkey: ECPoint) -> int:
        """Get vote count for a candidate, or -1 if candidate is not registered."""
        pubkey_bytes = self._pubkey_bytes(pubkey)
        if pubkey_bytes is None:
            return -1
        key = self._create_storage_key(PREFIX_CANDIDATE, pubkey_bytes)
        item = snapshot.get(key)
        if item is None:
            return -1
        state = CandidateState.from_bytes(item.value)
        return state.votes if state.registered else -1

    def get_committee(self, snapshot: Any) -> list[bytes]:
        """Get the current committee members."""
        key = self._create_storage_key(PREFIX_COMMITTEE)
        item = snapshot.get(key)
        if item is None:
            return []
        # Mirror C# GetCommittee (NeoToken.cs:576-579): the public keys are
        # returned sorted ascending (OrderBy(p => p)). The stored cache stays
        # in votes-descending order so get_next_block_validators can take the
        # top-N before its own sort.
        return sorted(self._parse_committee(item.value))

    def get_committee_address(self, snapshot: Any) -> UInt160:
        """Get committee multisig address from current committee membership."""
        committee = self.get_committee(snapshot)
        if not committee:
            return UInt160.ZERO

        threshold = len(committee) - (len(committee) - 1) // 3
        from neo.protocol_settings import ProtocolSettings

        script = ProtocolSettings._create_multisig_redeem_script(threshold, committee)
        return UInt160(hash160(script))

    def _parse_committee(self, data: bytes) -> list[bytes]:
        """Parse committee from serialized data."""
        if not data:
            return []
        committee = []
        offset = 0
        while offset < len(data):
            if offset + 33 <= len(data):
                committee.append(data[offset : offset + 33])
                offset += 33 + 32  # pubkey + votes
            else:
                break
        return committee

    def get_next_block_validators(self, engine: Any) -> list[bytes]:
        """Get validators for the next block.

        Takes the top validators_count members (highest votes) from the
        committee list (which is stored in votes-descending order by
        _refresh_committee), then sorts them by public key for
        deterministic block signing order.
        """
        committee = self.get_committee(engine.snapshot)
        validators_count = engine.protocol_settings.validators_count
        return sorted(committee[:validators_count])

    def get_account_state(self, snapshot: Any, account: UInt160) -> NeoAccountState | None:
        """Get account state for an account."""
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = snapshot.get(key)
        if item is None:
            return None
        return self._get_account_state(item)

    def on_nep17_payment(
        self, engine: Any, from_account: UInt160 | None, amount: int, data: Any
    ) -> None:
        """Handle GAS payments. Mirrors C# OnNEP17Payment (NeoToken.cs:374-389).

        Pre-Echidna this only enforces that the caller is the GAS contract.
        Post-Echidna it additionally registers a candidate (the public key is
        provided in ``data``) when the paid amount equals the register price,
        then burns the received GAS.
        """
        gas_contract = self.get_contract_by_name("GasToken")
        if gas_contract is None:
            return

        caller = getattr(engine, "calling_script_hash", None)
        if caller != gas_contract.hash:
            raise ValueError("Only GAS contract can call this method")

        if not self.is_hardfork_enabled(engine, Hardfork.HF_ECHIDNA):
            return

        register_price = self.get_register_price(engine.snapshot)
        if amount != register_price:
            raise ValueError(
                f"Incorrect GAS amount. Expected {register_price} GAS, "
                f"but received {amount} GAS."
            )

        pubkey_bytes = self._decode_pubkey_data(data)
        if pubkey_bytes is None:
            raise ValueError("Invalid candidate public key")

        if not self.register_internal(engine, pubkey_bytes):
            raise ValueError("Failed to register candidate")

        # Burn the received GAS from the NEO contract's balance.
        gas_contract.burn(engine, self.hash, amount)

    @staticmethod
    def _decode_pubkey_data(data: Any) -> bytes | None:
        """Decode an ECPoint from the onNEP17Payment data span.

        Returns the compressed 33-byte encoding, or None when the data is not
        a valid Secp256r1 point (C# DecodePoint throws on invalid input).
        """
        if isinstance(data, (bytes, bytearray, memoryview)):
            raw = bytes(data)
        elif hasattr(data, "get_span"):
            raw = bytes(data.get_span())
        elif hasattr(data, "value") and isinstance(data.value, (bytes, bytearray)):
            raw = bytes(data.value)
        else:
            return None
        from neo.crypto.ecc.curve import SECP256R1

        point = ECPoint.decode(raw, SECP256R1)
        return point.encode(compressed=True)

    def initialize(self, engine: Any) -> None:
        """Initialize NEO token on genesis."""
        # Initialize committee with standby committee (pubkey + votes=0 each),
        # mirroring C# InitializeAsync's CachedCommittee seed (NeoToken.cs:206).
        committee_key = self._create_storage_key(PREFIX_COMMITTEE)
        committee_data = bytearray()
        settings = getattr(engine, "protocol_settings", None)
        standby = getattr(settings, "standby_committee", []) if settings is not None else []
        for pubkey in standby:
            committee_data.extend(pubkey)
            committee_data.extend((0).to_bytes(32, "little", signed=True))
        engine.snapshot.add(committee_key, StorageItem(bytes(committee_data)))

        # Initialize voters count
        voters_key = self._create_storage_key(PREFIX_VOTERS_COUNT)
        engine.snapshot.add(voters_key, StorageItem())

        # Initialize gas per block (5 GAS)
        gas_key = self._create_storage_key(PREFIX_GAS_PER_BLOCK, 0)
        gas_item = StorageItem()
        gas_item.set(5 * 10**8)
        engine.snapshot.add(gas_key, gas_item)

        # Initialize register price (1000 GAS)
        price_key = self._create_storage_key(PREFIX_REGISTER_PRICE)
        price_item = StorageItem()
        price_item.set(1000 * 10**8)
        engine.snapshot.add(price_key, price_item)

    def on_persist(self, engine: Any) -> None:
        """Called when a block is being persisted.

        Mirrors C# OnPersistAsync (NeoToken.cs:222-249): recompute the
        committee when ShouldRefreshCommittee, capturing the previous
        membership so a CommitteeChanged notification can be emitted under
        HF_Cockatrice when the set of public keys changes.
        """
        m = engine.protocol_settings.committee_members_count
        if engine.persisting_block.index % m != 0:
            return
        self._refresh_committee(engine)

    def post_persist(self, engine: Any) -> None:
        """Distribute committee/voter GAS rewards after persistence.

        Mirrors C# PostPersistAsync (NeoToken.cs:253-284).
        """
        m = engine.protocol_settings.committee_members_count
        n = engine.protocol_settings.validators_count
        block_index = engine.persisting_block.index
        index = block_index % m
        gas_per_block = self.get_gas_per_block(engine.snapshot)

        committee = self._parse_committee_pairs(
            self._committee_storage_value(engine.snapshot)
        )
        if not committee:
            return

        # Per-block reward to the committee member whose turn it is.
        member_pubkey = committee[index][0]
        from neo.smartcontract.syscalls.contract import (
            _create_signature_redeem_script,
        )

        member_script = _create_signature_redeem_script(member_pubkey)
        member_account = UInt160(hash160(member_script))
        self._mint_gas(
            engine, member_account, gas_per_block * COMMITTEE_REWARD_RATIO // 100, False
        )

        # Accumulate voter rewards when the committee is refreshed.
        if block_index % m != 0:
            return
        voter_reward_of_each_committee = (
            gas_per_block * VOTER_REWARD_RATIO * VOTE_FACTOR * m // (m + n) // 100
        )
        for i, (pubkey, votes) in enumerate(committee):
            factor = 2 if i < n else 1  # validators' voters earn double
            if votes > 0:
                voter_sum_reward_per_neo = factor * voter_reward_of_each_committee // votes
                reward_key = self._create_storage_key(
                    PREFIX_VOTER_REWARD_PER_COMMITTEE, pubkey
                )
                reward_item = engine.snapshot.get_and_change(
                    reward_key, lambda: StorageItem()
                )
                reward_item.add(voter_sum_reward_per_neo)

    def _committee_storage_value(self, snapshot: Any) -> bytes:
        """Return the raw stored committee bytes (votes-descending cache order)."""
        key = self._create_storage_key(PREFIX_COMMITTEE)
        item = snapshot.get(key)
        return item.value if item is not None else b""

    def _refresh_committee(self, engine: Any) -> None:
        """Refresh the committee based on current votes.

        Mirrors C# ComputeCommitteeMembers (NeoToken.cs:622-635): falls back to
        the StandbyCommittee when voter turnout is below the effective
        threshold or there are fewer candidates than committee seats; otherwise
        selects the top-N candidates by (votes desc, pubkey).
        """
        key = self._create_storage_key(PREFIX_COMMITTEE)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())

        prev_committee = [pubkey for pubkey, _votes in self._parse_committee_pairs(item.value)]

        new_committee = self._compute_committee_members(engine)

        # Serialize committee data: pubkey (33 bytes) + votes (32 bytes) for each
        committee_data = bytearray()
        for pubkey, votes in new_committee:
            committee_data.extend(pubkey)
            committee_data.extend(votes.to_bytes(32, "little", signed=True))
        item.value = bytes(committee_data)

        # HF_Cockatrice CommitteeChanged notification (NeoToken.cs:233-247).
        if self.is_hardfork_enabled(engine, Hardfork.HF_COCKATRICE):
            new_keys = [pubkey for pubkey, _votes in new_committee]
            if new_keys != prev_committee:
                engine.send_notification(
                    self.hash,
                    "CommitteeChanged",
                    [list(prev_committee), list(new_keys)],
                )

    def _compute_committee_members(self, engine: Any) -> list[tuple[bytes, int]]:
        """Mirror C# ComputeCommitteeMembers (NeoToken.cs:622-635)."""
        snapshot = engine.snapshot
        committee_count = engine.protocol_settings.committee_members_count

        voters_key = self._create_storage_key(PREFIX_VOTERS_COUNT)
        voters_item = snapshot.get(voters_key)
        voters_count = int(voters_item) if voters_item else 0
        # voter_turnout = votersCount / TotalAmount; compare against 0.2
        # without floating point loss: votersCount / TotalAmount < 0.2.
        below_turnout = voters_count * 5 < self._total_amount

        candidates = self.get_candidates(snapshot)

        if below_turnout or len(candidates) < committee_count:
            votes_by_key = {pubkey: votes for pubkey, votes in candidates}
            return [
                (pubkey, votes_by_key.get(pubkey, 0))
                for pubkey in engine.protocol_settings.standby_committee
            ]

        ordered = sorted(candidates, key=lambda x: (-x[1], x[0]))
        return ordered[:committee_count]

    def _parse_committee_pairs(self, data: bytes) -> list[tuple[bytes, int]]:
        """Parse stored committee into (pubkey, votes) pairs."""
        if not data:
            return []
        pairs: list[tuple[bytes, int]] = []
        offset = 0
        while offset + 33 + 32 <= len(data):
            pubkey = data[offset : offset + 33]
            votes = int.from_bytes(data[offset + 33 : offset + 65], "little", signed=True)
            pairs.append((pubkey, votes))
            offset += 33 + 32
        return pairs
