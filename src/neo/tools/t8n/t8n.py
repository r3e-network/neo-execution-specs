"""Neo t8n (transition) tool - Main logic.

Executes transactions against a pre-state and produces post-state.
"""

from __future__ import annotations
from typing import Dict, List, Any

from neo.tools.t8n.types import (
    Alloc,
    AccountState,
    Environment,
    TransactionInput,
    T8NResult,
    T8NOutput,
    Receipt,
)
from neo.persistence.snapshot import MemorySnapshot
from neo.crypto.hash import hash256


# Storage key prefixes (matching Neo N3)
PREFIX_CONTRACT = 0x08
PREFIX_STORAGE = 0x70
PREFIX_NEO_BALANCE = 0x14
PREFIX_GAS_BALANCE = 0x14


def _hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes."""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)


def _bytes_to_hex(data: bytes) -> str:
    """Convert bytes to hex string."""
    return "0x" + data.hex()


class T8N:
    """Neo state transition tool.
    
    Executes transactions against a pre-state allocation
    and produces the resulting post-state.
    """
    
    def __init__(
        self,
        alloc: Dict[str, Any],
        env: Dict[str, Any],
        txs: List[Dict[str, Any]],
    ):
        """Initialize t8n with input data.
        
        Args:
            alloc: Pre-state allocation (address -> account state)
            env: Block environment
            txs: List of transactions to execute
        """
        self.pre_alloc = self._parse_alloc(alloc)
        self.env = Environment.from_dict(env)
        self.txs = [TransactionInput.from_dict(tx) for tx in txs]
        self.snapshot = MemorySnapshot()
        self.receipts: List[Receipt] = []
        self.total_gas_used = 0
    
    def _parse_alloc(self, alloc: Dict[str, Any]) -> Alloc:
        """Parse allocation dictionary."""
        result: Alloc = {}
        for addr, state in alloc.items():
            result[addr] = AccountState.from_dict(state)
        return result
    
    def _init_state(self) -> None:
        """Initialize snapshot from pre-state allocation."""
        for addr, state in self.pre_alloc.items():
            addr_bytes = _hex_to_bytes(addr)
            
            # Store GAS balance
            if state.gas_balance > 0:
                key = bytes([PREFIX_GAS_BALANCE]) + addr_bytes
                value = state.gas_balance.to_bytes(8, 'little')
                self.snapshot.put(key, value)
            
            # Store storage entries
            for storage_key, storage_value in state.storage.items():
                key = bytes([PREFIX_STORAGE]) + addr_bytes + _hex_to_bytes(storage_key)
                self.snapshot.put(key, _hex_to_bytes(storage_value))
    
    def _execute_tx(self, tx: TransactionInput, index: int) -> Receipt:
        """Execute a single transaction."""
        from neo.vm.execution_engine import ExecutionEngine, VMState
        
        script = _hex_to_bytes(tx.script)
        tx_hash = _bytes_to_hex(hash256(script + index.to_bytes(4, 'little')))
        
        # Create execution engine
        engine = ExecutionEngine()
        engine.load_script(script)
        
        # Execute
        try:
            state = engine.execute()
            vm_state = "HALT" if state == VMState.HALT else "FAULT"
            exception = None
        except Exception as e:
            vm_state = "FAULT"
            exception = str(e)
        
        # Get gas consumed (simplified)
        gas_consumed = tx.system_fee if tx.system_fee > 0 else 1000000
        self.total_gas_used += gas_consumed
        
        # Build receipt
        return Receipt(
            tx_hash=tx_hash,
            vm_state=vm_state,
            gas_consumed=gas_consumed,
            exception=exception,
            stack=[],
            notifications=[],
        )
    
    def _extract_post_alloc(self) -> Dict[str, Dict[str, Any]]:
        """Extract post-state allocation from snapshot."""
        result: Dict[str, Dict[str, Any]] = {}
        
        # Copy pre-state and update with changes
        for addr, state in self.pre_alloc.items():
            result[addr] = state.to_dict()
        
        return result
    
    def _compute_state_root(self) -> str:
        """Compute state root hash."""
        # Simplified: hash all committed data
        data = b""
        for key, value in sorted(self.snapshot._store.items()):
            data += key + value
        if not data:
            data = b"\x00"
        return _bytes_to_hex(hash256(data))
    
    def run(self) -> T8NOutput:
        """Execute all transactions and return result."""
        # Initialize state
        self._init_state()
        
        # Execute transactions
        for i, tx in enumerate(self.txs):
            receipt = self._execute_tx(tx, i)
            self.receipts.append(receipt)
        
        # Commit changes
        self.snapshot.commit()
        
        # Build result
        state_root = self._compute_state_root()
        post_alloc = self._extract_post_alloc()
        
        result = T8NResult(
            state_root=state_root,
            receipts=self.receipts,
            gas_used=self.total_gas_used,
        )
        
        return T8NOutput(result=result, alloc=post_alloc)
