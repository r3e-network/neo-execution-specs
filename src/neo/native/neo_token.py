"""NEO Token native contract."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from neo.types import UInt160
from neo.native.fungible_token import FungibleToken, AccountState, PREFIX_ACCOUNT
from neo.native.native_contract import CallFlags, StorageItem


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
    vote_to: Optional[bytes] = None  # ECPoint encoded
    last_gas_per_vote: int = 0
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        data = self.balance.to_bytes(32, 'little', signed=True)
        data += self.balance_height.to_bytes(4, 'little')
        if self.vote_to:
            data += bytes([len(self.vote_to)]) + self.vote_to
        else:
            data += bytes([0])
        data += self.last_gas_per_vote.to_bytes(32, 'little', signed=True)
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NeoAccountState':
        """Deserialize from bytes."""
        state = cls()
        if not data:
            return state
        state.balance = int.from_bytes(data[:32], 'little', signed=True)
        if len(data) > 32:
            state.balance_height = int.from_bytes(data[32:36], 'little')
        if len(data) > 36:
            vote_len = data[36]
            if vote_len > 0:
                state.vote_to = data[37:37+vote_len]
            offset = 37 + vote_len
            if len(data) > offset:
                state.last_gas_per_vote = int.from_bytes(
                    data[offset:offset+32], 'little', signed=True)
        return state


@dataclass
class CandidateState:
    """State for a candidate."""
    registered: bool = False
    votes: int = 0
    
    def to_bytes(self) -> bytes:
        data = bytes([1 if self.registered else 0])
        data += self.votes.to_bytes(32, 'little', signed=True)
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'CandidateState':
        state = cls()
        if data:
            state.registered = data[0] == 1
            if len(data) > 1:
                state.votes = int.from_bytes(data[1:33], 'little', signed=True)
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
    def total_supply(self) -> int:
        return self._total_amount
    
    def _register_methods(self) -> None:
        """Register NEO-specific methods."""
        super()._register_methods()
        self._register_method("unclaimedGas", self.unclaimed_gas, 
                            cpu_fee=1 << 17, call_flags=CallFlags.READ_STATES)
        self._register_method("getGasPerBlock", self.get_gas_per_block,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setGasPerBlock", self.set_gas_per_block,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("getRegisterPrice", self.get_register_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setRegisterPrice", self.set_register_price,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("registerCandidate", self.register_candidate,
                            call_flags=CallFlags.STATES)
        self._register_method("unregisterCandidate", self.unregister_candidate,
                            cpu_fee=1 << 16, call_flags=CallFlags.STATES)
        self._register_method("vote", self.vote,
                            cpu_fee=1 << 16, call_flags=CallFlags.STATES)
        self._register_method("getCandidates", self.get_candidates,
                            cpu_fee=1 << 22, call_flags=CallFlags.READ_STATES)
        self._register_method("getCommittee", self.get_committee,
                            cpu_fee=1 << 16, call_flags=CallFlags.READ_STATES)
        self._register_method("getNextBlockValidators", self.get_next_block_validators,
                            cpu_fee=1 << 16, call_flags=CallFlags.READ_STATES)
        self._register_method("getAccountState", self.get_account_state,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
    
    def get_total_supply(self, snapshot: Any) -> int:
        """NEO has fixed supply."""
        return self._total_amount
    
    def _get_account_state(self, item: StorageItem) -> NeoAccountState:
        """Get NEO account state from storage item."""
        return NeoAccountState.from_bytes(item.value)
    
    def _create_account_state(self) -> NeoAccountState:
        """Create a new NEO account state."""
        return NeoAccountState()
    
    def get_gas_per_block(self, snapshot: Any) -> int:
        """Get the amount of GAS generated per block."""
        key = self._create_storage_key(PREFIX_GAS_PER_BLOCK)
        item = snapshot.get(key)
        return int(item) if item else 5 * 10**8  # Default 5 GAS
    
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
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = engine.snapshot.get(key)
        if item is None:
            return 0
        state = self._get_account_state(item)
        return self._calculate_bonus(engine.snapshot, state, end)
    
    def _calculate_bonus(self, snapshot: Any, state: NeoAccountState, end: int) -> int:
        """Calculate GAS bonus for holding NEO."""
        if state.balance == 0:
            return 0
        if state.balance_height >= end:
            return 0
        
        # Calculate NEO holder reward
        gas_per_block = self.get_gas_per_block(snapshot)
        blocks = end - state.balance_height
        neo_holder_reward = (state.balance * gas_per_block * blocks * 
                           NEO_HOLDER_REWARD_RATIO // 100 // self._total_amount)
        
        # Calculate vote reward if voting
        vote_reward = 0
        if state.vote_to is not None:
            key = self._create_storage_key(PREFIX_VOTER_REWARD_PER_COMMITTEE, state.vote_to)
            item = snapshot.get(key)
            if item:
                latest_gas_per_vote = int(item)
                vote_reward = (state.balance * (latest_gas_per_vote - state.last_gas_per_vote) 
                              // VOTE_FACTOR)
        
        return neo_holder_reward + vote_reward
    
    def register_candidate(self, engine: Any, pubkey: bytes) -> bool:
        """Register as a candidate."""
        if not engine.check_witness_pubkey(pubkey):
            return False
        
        # Charge registration fee
        engine.add_fee(self.get_register_price(engine.snapshot))
        
        key = self._create_storage_key(PREFIX_CANDIDATE, pubkey)
        item = engine.snapshot.get_and_change(
            key, lambda: StorageItem(CandidateState().to_bytes()))
        state = CandidateState.from_bytes(item.value)
        
        if state.registered:
            return True
        
        state.registered = True
        item.value = state.to_bytes()
        
        engine.send_notification(
            self.hash, "CandidateStateChanged", 
            [pubkey, True, state.votes])
        return True
    
    def unregister_candidate(self, engine: Any, pubkey: bytes) -> bool:
        """Unregister as a candidate."""
        if not engine.check_witness_pubkey(pubkey):
            return False
        
        key = self._create_storage_key(PREFIX_CANDIDATE, pubkey)
        item = engine.snapshot.get(key)
        if item is None:
            return True
        
        item = engine.snapshot.get_and_change(key)
        state = CandidateState.from_bytes(item.value)
        if not state.registered:
            return True
        
        state.registered = False
        item.value = state.to_bytes()
        self._check_candidate(engine.snapshot, pubkey, state)
        
        engine.send_notification(
            self.hash, "CandidateStateChanged", 
            [pubkey, False, state.votes])
        return True
    
    def _check_candidate(self, snapshot: Any, pubkey: bytes, 
                         candidate: CandidateState) -> None:
        """Remove candidate if unregistered and has no votes."""
        if not candidate.registered and candidate.votes == 0:
            key = self._create_storage_key(PREFIX_CANDIDATE, pubkey)
            snapshot.delete(key)
            reward_key = self._create_storage_key(
                PREFIX_VOTER_REWARD_PER_COMMITTEE, pubkey)
            snapshot.delete(reward_key)
    
    def vote(self, engine: Any, account: UInt160, 
             vote_to: Optional[bytes]) -> bool:
        """Vote for a candidate."""
        if not engine.check_witness(account):
            return False
        
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = engine.snapshot.get_and_change(key)
        if item is None:
            return False
        
        state = self._get_account_state(item)
        if state.balance == 0:
            return False
        
        # Validate new candidate
        if vote_to is not None:
            cand_key = self._create_storage_key(PREFIX_CANDIDATE, vote_to)
            cand_item = engine.snapshot.get(cand_key)
            if cand_item is None:
                return False
            cand_state = CandidateState.from_bytes(cand_item.value)
            if not cand_state.registered:
                return False
        
        # Update voters count
        voters_key = self._create_storage_key(PREFIX_VOTERS_COUNT)
        if (state.vote_to is None) != (vote_to is None):
            voters_item = engine.snapshot.get_and_change(
                voters_key, lambda: StorageItem())
            if state.vote_to is None:
                voters_item.add(state.balance)
            else:
                voters_item.add(-state.balance)
        
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
        
        # Add votes to new candidate
        state.vote_to = vote_to
        if vote_to is not None:
            new_key = self._create_storage_key(PREFIX_CANDIDATE, vote_to)
            new_item = engine.snapshot.get_and_change(new_key)
            new_cand = CandidateState.from_bytes(new_item.value)
            new_cand.votes += state.balance
            new_item.value = new_cand.to_bytes()
        
        item.value = state.to_bytes()
        engine.send_notification(
            self.hash, "Vote", 
            [account, old_vote, vote_to, state.balance])
        return True
    
    def get_candidates(self, snapshot: Any) -> List[Tuple[bytes, int]]:
        """Get all registered candidates with their votes."""
        candidates = []
        prefix = self._create_storage_key(PREFIX_CANDIDATE)
        for key, item in snapshot.find(prefix):
            state = CandidateState.from_bytes(item.value)
            if state.registered:
                pubkey = key.key[1:]  # Remove prefix
                candidates.append((pubkey, state.votes))
        return candidates[:256]  # Max 256 candidates
    
    def get_committee(self, snapshot: Any) -> List[bytes]:
        """Get the current committee members."""
        key = self._create_storage_key(PREFIX_COMMITTEE)
        item = snapshot.get(key)
        if item is None:
            return []
        return self._parse_committee(item.value)
    
    def _parse_committee(self, data: bytes) -> List[bytes]:
        """Parse committee from serialized data."""
        if not data:
            return []
        committee = []
        offset = 0
        while offset < len(data):
            if offset + 33 <= len(data):
                committee.append(data[offset:offset+33])
                offset += 33 + 32  # pubkey + votes
            else:
                break
        return sorted(committee)
    
    def get_next_block_validators(self, engine: Any) -> List[bytes]:
        """Get validators for the next block."""
        committee = self.get_committee(engine.snapshot)
        validators_count = engine.protocol_settings.validators_count
        return sorted(committee[:validators_count])
    
    def get_account_state(self, snapshot: Any, 
                          account: UInt160) -> Optional[NeoAccountState]:
        """Get account state for an account."""
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = snapshot.get(key)
        if item is None:
            return None
        return self._get_account_state(item)
    
    def initialize(self, engine: Any) -> None:
        """Initialize NEO token on genesis."""
        # Initialize committee with standby committee
        committee_key = self._create_storage_key(PREFIX_COMMITTEE)
        engine.snapshot.add(committee_key, StorageItem())
        
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
        """Called when a block is being persisted."""
        # Refresh committee if needed
        m = engine.protocol_settings.committee_members_count
        if engine.persisting_block.index % m == 0:
            self._refresh_committee(engine)
    
    def _refresh_committee(self, engine: Any) -> None:
        """Refresh the committee based on current votes.
        
        Selects the top N candidates by votes to form the new committee,
        where N is the committee_members_count from protocol settings.
        """
        # Get all candidates with their votes
        candidates = self.get_candidates(engine.snapshot)
        
        # Sort by votes (descending), then by public key for determinism
        candidates.sort(key=lambda x: (-x[1], x[0]))
        
        # Get committee size from protocol settings
        committee_count = engine.protocol_settings.committee_members_count
        
        # Select top candidates for committee
        new_committee = candidates[:committee_count]
        
        # Serialize committee data: pubkey (33 bytes) + votes (32 bytes) for each
        committee_data = bytearray()
        for pubkey, votes in new_committee:
            committee_data.extend(pubkey)
            committee_data.extend(votes.to_bytes(32, 'little', signed=True))
        
        # Store new committee
        key = self._create_storage_key(PREFIX_COMMITTEE)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        item.value = bytes(committee_data)
