"""Comprehensive tests for NEO and GAS tokens."""

import pytest
from neo.native.neo_token import NeoToken, NeoAccountState, CandidateState
from neo.native.gas_token import GasToken
from neo.types import UInt160


class TestNeoToken:
    """Tests for NEO token."""
    
    def setup_method(self):
        self.neo = NeoToken()
    
    def test_properties(self):
        """Test NEO token properties."""
        assert self.neo.name == "NeoToken"
        assert self.neo.symbol == "NEO"
        assert self.neo.decimals == 0
        assert self.neo.total_supply == 100_000_000
    
    def test_total_amount(self):
        """Test total amount constant."""
        assert self.neo.TOTAL_AMOUNT == 100_000_000


class TestNeoAccountState:
    """Tests for NEO account state."""
    
    def test_default_state(self):
        """Test default account state."""
        state = NeoAccountState()
        assert state.balance == 0
        assert state.balance_height == 0
        assert state.vote_to is None
        assert state.last_gas_per_vote == 0
    
    def test_serialization(self):
        """Test account state serialization."""
        state = NeoAccountState()
        state.balance = 1000
        state.balance_height = 100
        
        data = state.to_bytes()
        assert len(data) > 0
        
        recovered = NeoAccountState.from_bytes(data)
        assert recovered.balance == 1000
        assert recovered.balance_height == 100
    
    def test_with_vote(self):
        """Test account state with vote."""
        state = NeoAccountState()
        state.balance = 500
        state.vote_to = b'\x02' + b'\x00' * 32  # Fake pubkey
        
        data = state.to_bytes()
        recovered = NeoAccountState.from_bytes(data)
        assert recovered.vote_to == state.vote_to


class TestCandidateState:
    """Tests for candidate state."""
    
    def test_default_state(self):
        """Test default candidate state."""
        state = CandidateState()
        assert state.registered == False
        assert state.votes == 0
    
    def test_serialization(self):
        """Test candidate state serialization."""
        state = CandidateState()
        state.registered = True
        state.votes = 1000000
        
        data = state.to_bytes()
        recovered = CandidateState.from_bytes(data)
        
        assert recovered.registered == True
        assert recovered.votes == 1000000


class TestGasToken:
    """Tests for GAS token."""
    
    def setup_method(self):
        self.gas = GasToken()
    
    def test_properties(self):
        """Test GAS token properties."""
        assert self.gas.name == "GasToken"
        assert self.gas.symbol == "GAS"
        assert self.gas.decimals == 8
    
    def test_initial_supply(self):
        """Test GAS initial supply."""
        # GAS has 30M initial supply
        assert self.gas.INITIAL_GAS == 30_000_000 * 10**8
