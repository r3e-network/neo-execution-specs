"""Extended tests for NeoToken native contract."""

from neo.native.neo_token import NeoToken, NeoAccountState, CandidateState


class TestNeoAccountState:
    """Tests for NeoAccountState class."""
    
    def test_create_default(self):
        """Test creating default account state."""
        state = NeoAccountState()
        assert state.balance == 0
        assert state.balance_height == 0
        assert state.vote_to is None
        assert state.last_gas_per_vote == 0
    
    def test_create_with_values(self):
        """Test creating account state with values."""
        state = NeoAccountState(
            balance=100,
            balance_height=1000,
            vote_to=bytes(33),
            last_gas_per_vote=500
        )
        assert state.balance == 100
        assert state.balance_height == 1000
        assert state.vote_to == bytes(33)
        assert state.last_gas_per_vote == 500
    
    def test_to_bytes_empty(self):
        """Test serializing empty state."""
        state = NeoAccountState()
        data = state.to_bytes()
        assert len(data) > 0
    
    def test_from_bytes_empty(self):
        """Test deserializing empty data."""
        state = NeoAccountState.from_bytes(b"")
        assert state.balance == 0
    
    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = NeoAccountState(
            balance=12345,
            balance_height=999,
            vote_to=bytes(33),
            last_gas_per_vote=777
        )
        data = original.to_bytes()
        restored = NeoAccountState.from_bytes(data)
        assert restored.balance == original.balance
        assert restored.balance_height == original.balance_height
        assert restored.vote_to == original.vote_to
        assert restored.last_gas_per_vote == original.last_gas_per_vote


class TestCandidateState:
    """Tests for CandidateState class."""
    
    def test_create_default(self):
        """Test creating default candidate state."""
        state = CandidateState()
        assert state.registered is False
        assert state.votes == 0
    
    def test_create_registered(self):
        """Test creating registered candidate."""
        state = CandidateState(registered=True, votes=1000)
        assert state.registered is True
        assert state.votes == 1000
    
    def test_to_bytes(self):
        """Test serializing candidate state."""
        state = CandidateState(registered=True, votes=500)
        data = state.to_bytes()
        assert len(data) > 0
    
    def test_from_bytes_empty(self):
        """Test deserializing empty data."""
        state = CandidateState.from_bytes(b"")
        assert state.registered is False
        assert state.votes == 0
    
    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = CandidateState(registered=True, votes=99999)
        data = original.to_bytes()
        restored = CandidateState.from_bytes(data)
        assert restored.registered == original.registered
        assert restored.votes == original.votes


class TestNeoToken:
    """Tests for NeoToken class."""
    
    def test_name(self):
        """Test token name."""
        token = NeoToken()
        assert token.name == "NeoToken"
    
    def test_symbol(self):
        """Test token symbol."""
        token = NeoToken()
        assert token.symbol == "NEO"
    
    def test_decimals(self):
        """Test token decimals."""
        token = NeoToken()
        assert token.decimals == 0
    
    def test_total_supply(self):
        """Test total supply."""
        token = NeoToken()
        assert token.total_supply == 100_000_000
    
    def test_total_amount(self):
        """Test total amount."""
        token = NeoToken()
        assert token.total_amount == 100_000_000
