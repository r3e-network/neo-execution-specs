"""Tests for Neo t8n tool."""

import pytest
from neo.tools.t8n import T8N
from neo.tools.t8n.types import (
    AccountState,
    Environment,
    TransactionInput,
)


class TestTypes:
    """Test type parsing."""
    
    def test_account_state_from_dict(self):
        data = {
            "gasBalance": 1000000,
            "neoBalance": 100,
            "storage": {"0a": "0b"},
        }
        state = AccountState.from_dict(data)
        assert state.gas_balance == 1000000
        assert state.neo_balance == 100
        assert state.storage == {"0a": "0b"}
    
    def test_account_state_to_dict(self):
        state = AccountState(gas_balance=500, neo_balance=10)
        d = state.to_dict()
        assert d["gasBalance"] == 500
        assert d["neoBalance"] == 10
    
    def test_environment_from_dict(self):
        data = {"currentBlockNumber": 100, "timestamp": 12345}
        env = Environment.from_dict(data)
        assert env.current_block_number == 100
        assert env.timestamp == 12345


class TestT8N:
    """Test t8n execution."""
    
    def test_empty_execution(self):
        """Test with no transactions."""
        alloc = {}
        env = {"currentBlockNumber": 1}
        txs = []
        
        t8n = T8N(alloc=alloc, env=env, txs=txs)
        output = t8n.run()
        
        assert output.result.gas_used == 0
        assert len(output.result.receipts) == 0
    
    def test_simple_transaction(self):
        """Test with a simple transaction."""
        alloc = {
            "0000000000000000000000000000000000000001": {
                "gasBalance": 10000000
            }
        }
        env = {"currentBlockNumber": 100}
        # Simple PUSH1 + RET script
        txs = [{"script": "1100", "signers": []}]
        
        t8n = T8N(alloc=alloc, env=env, txs=txs)
        output = t8n.run()
        
        assert len(output.result.receipts) == 1
        assert output.result.gas_used > 0
    
    def test_state_initialization(self):
        """Test state is properly initialized."""
        alloc = {
            "0000000000000000000000000000000000000001": {
                "gasBalance": 5000000,
                "storage": {"aa": "bb"}
            }
        }
        env = {"currentBlockNumber": 1}
        txs = []
        
        t8n = T8N(alloc=alloc, env=env, txs=txs)
        t8n._init_state()
        
        # Verify state was initialized
        assert len(t8n.snapshot._changes) > 0
