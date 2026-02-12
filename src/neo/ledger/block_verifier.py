"""
Block Verifier - Block verification logic.

Reference: Neo.Ledger.Blockchain (verification parts)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from neo.ledger.transaction_verifier import TransactionVerifier
from neo.ledger.verify_result import VerifyResult

if TYPE_CHECKING:
    from neo.network.payloads.block import Block
    from neo.persistence.snapshot import Snapshot


class BlockVerifier:
    """Verifies blocks for validity."""

    @staticmethod
    def verify(
        block: "Block",
        snapshot: "Snapshot",
        prev_block: Optional["Block"] = None,
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
        result = BlockVerifier.verify_structure(block)
        if result != VerifyResult.SUCCEED:
            return result

        result = BlockVerifier.verify_chain_link(block, prev_block)
        if result != VerifyResult.SUCCEED:
            return result

        if not BlockVerifier.verify_merkle_root(block):
            return VerifyResult.INVALID

        for tx in block.transactions:
            result = TransactionVerifier.verify_state_independent(tx)
            if result != VerifyResult.SUCCEED:
                return result

        return VerifyResult.SUCCEED

    @staticmethod
    def verify_structure(block: "Block") -> VerifyResult:
        """Verify block structure."""
        if block.version > 0:
            return VerifyResult.INVALID

        if block.witness is None:
            return VerifyResult.INVALID

        return VerifyResult.SUCCEED

    @staticmethod
    def verify_chain_link(
        block: "Block",
        prev_block: Optional["Block"],
    ) -> VerifyResult:
        """Verify block links to previous block."""
        if block.index == 0:
            return VerifyResult.SUCCEED

        if prev_block is None:
            return VerifyResult.INVALID

        prev_hash = block.prev_hash.data if hasattr(block.prev_hash, "data") else bytes(block.prev_hash)
        expected_prev_hash = prev_block.hash.data if hasattr(prev_block.hash, "data") else bytes(prev_block.hash)
        if prev_hash != expected_prev_hash:
            return VerifyResult.INVALID

        if block.index != prev_block.index + 1:
            return VerifyResult.INVALID

        if block.timestamp <= prev_block.timestamp:
            return VerifyResult.INVALID

        return VerifyResult.SUCCEED

    @staticmethod
    def verify_merkle_root(block: "Block") -> bool:
        """Verify the merkle root matches transactions."""
        from neo.crypto.merkle_tree import MerkleTree

        if not block.transactions:
            if hasattr(block.merkle_root, "is_zero"):
                return block.merkle_root.is_zero()
            return True

        tx_hashes = [tx.hash.data if hasattr(tx.hash, "data") else bytes(tx.hash) for tx in block.transactions]
        calculated_root = MerkleTree.compute_root(tx_hashes)
        merkle_root = block.merkle_root.data if hasattr(block.merkle_root, "data") else bytes(block.merkle_root)

        return merkle_root == calculated_root
