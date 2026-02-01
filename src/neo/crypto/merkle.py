"""
Merkle Tree implementation.

Reference: Neo.Cryptography.MerkleTree
"""

from typing import List
from neo.crypto.hash import hash256


def compute_root(hashes: List[bytes]) -> bytes:
    """Compute Merkle root from list of hashes."""
    if not hashes:
        return b'\x00' * 32
    
    if len(hashes) == 1:
        return hashes[0]
    
    # Build tree bottom-up
    tree = list(hashes)
    while len(tree) > 1:
        if len(tree) % 2 == 1:
            tree.append(tree[-1])
        
        next_level = []
        for i in range(0, len(tree), 2):
            combined = tree[i] + tree[i + 1]
            next_level.append(hash256(combined))
        tree = next_level
    
    return tree[0]
