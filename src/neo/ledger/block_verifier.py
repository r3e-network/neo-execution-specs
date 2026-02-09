"""
Block Verifier - Block verification logic.

Reference: Neo.Ledger.Blockchain (verification parts)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from neo.ledger.verify_result import VerifyResult
from neo.ledger.transaction_verifier import TransactionVerifier

if TYPE_CHECKING:
    from neo.network.payloads.block import Block
    from neo.persistence.snapshot import Snapshot


class BlockVerifier:
    """Verifies blocks for validity."""
    
    @staticmethod
    def verify(
        block: "Block",
        snapshot: "Snapshot",
        prev_block: Optional["Block"] = None
    ) -> VerifyResult:
        """
        Verify a block.
        
        Checks:
        - Block structure
        - Previous block link
        - Merkle root
        - Timestamp
        - Transactions
        """
        # Verify structure
        result = BlockVerifier.verify_structure(block)
        if result != VerifyResult.SUCCEED:
            return result
        
        # Verify chain link
        result = BlockVerifier.verify_chain_link(block, prev_block)
        if result != VerifyResult.SUCCEED:
            return result
        
        # Verify merkle root
        if not BlockVerifier.verify_merkle_root(block):
            return VerifyResult.INVALID
        
        # Verify all transactions
        for tx in block.transactions:
            result = TransactionVerifier.verify_state_independent(tx)
            if result != VerifyResult.SUCCEED:
                return result
        
        return VerifyResult.SUCCEED
    
    @staticmethod
    def verify_structure(block: "Block") -> VerifyResult:
        """Verify block structure."""
        # Check version
        if block.version > 0:
            return VerifyResult.INVALID
        
        # Check witness
        if block.witness is None:
            return VerifyResult.INVALID
        
        return VerifyResult.SUCCEED
    
    @staticmethod
    def verify_chain_link(
        block: "Block",
        prev_block: Optional["Block"]
    ) -> VerifyResult:
        """Verify block links to previous block."""
        if block.index == 0:
            # Genesis block
            return VerifyResult.SUCCEED
        
        if prev_block is None:
            return VerifyResult.INVALID
        
        # Check prev_hash
        if block.prev_hash != prev_block.hash:
            return VerifyResult.INVALID
        
        # Check index
        if block.index != prev_block.index + 1:
            return VerifyResult.INVALID
        
        # Check timestamp
        if block.timestamp <= prev_block.timestamp:
            return VerifyResult.INVALID
        
        return VerifyResult.SUCCEED
    
    @staticmethod
    def verify_merkle_root(block: "Block") -> bool:
        """Verify the merkle root matches transactions."""
        from neo.crypto.merkle_tree import MerkleTree
        
        if not block.transactions:
            # Empty block - merkle root should be zero
            return block.merkle_root.is_zero() if hasattr(block.merkle_root, 'is_zero') else True
        
        # Calculate merkle root from transactions
        tx_hashes = [tx.hash for tx in block.transactions]
        calculated_root = MerkleTree.compute_root(tx_hashes)
        
        return block.merkle_root == calculated_root
