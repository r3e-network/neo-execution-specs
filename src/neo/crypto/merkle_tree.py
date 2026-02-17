"""Neo N3 Merkle Tree.

Reference: Neo.Cryptography.MerkleTree
"""

from __future__ import annotations

from neo.crypto.hash import hash256

def compute_root(hashes: list[bytes]) -> bytes:
    """Compute merkle root from list of hashes."""
    if not hashes:
        return bytes(32)
    working = list(hashes)
    while len(working) > 1:
        if len(working) % 2 == 1:
            working.append(working[-1])
        working = [hash256(working[i] + working[i+1]) 
                   for i in range(0, len(working), 2)]
    return working[0]

class MerkleTree:
    """Merkle tree implementation."""
    
    def __init__(self, hashes: list[bytes]) -> None:
        """Initialize merkle tree from leaf hashes."""
        self._leaves = list(hashes)
        self._root: bytes | None = None
    
    @property
    def root(self) -> bytes:
        """Get the merkle root."""
        if self._root is None:
            self._root = compute_root(self._leaves)
        return self._root
    
    @staticmethod
    def compute_root(hashes: list[bytes]) -> bytes:
        """Compute merkle root from list of hashes."""
        return compute_root(hashes)
    
    @staticmethod
    def compute_root_from_data(data_list: list[bytes]) -> bytes:
        """Compute merkle root from list of data (hashes each item first)."""
        hashes = [hash256(d) for d in data_list]
        return compute_root(hashes)
    
    def get_proof(self, index: int) -> list[bytes]:
        """Get merkle proof for leaf at index."""
        if index < 0 or index >= len(self._leaves):
            raise IndexError("Index out of range")
        
        proof = []
        working = list(self._leaves)
        idx = index
        
        while len(working) > 1:
            if len(working) % 2 == 1:
                working.append(working[-1])
            
            # Get sibling
            sibling_idx = idx ^ 1
            proof.append(working[sibling_idx])
            
            # Move to next level
            working = [hash256(working[i] + working[i+1]) 
                       for i in range(0, len(working), 2)]
            idx //= 2
        
        return proof
    
    @staticmethod
    def verify_proof(
        leaf_hash: bytes,
        proof: list[bytes],
        root: bytes,
        index: int
    ) -> bool:
        """Verify a merkle proof."""
        current = leaf_hash
        idx = index
        
        for sibling in proof:
            if idx % 2 == 0:
                current = hash256(current + sibling)
            else:
                current = hash256(sibling + current)
            idx //= 2
        
        return current == root
