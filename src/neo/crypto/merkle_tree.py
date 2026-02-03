"""Neo N3 Merkle Tree."""

from typing import List
from neo.crypto.hash import hash256


def compute_root(hashes: List[bytes]) -> bytes:
    """Compute merkle root."""
    if not hashes:
        return bytes(32)
    while len(hashes) > 1:
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])
        hashes = [hash256(hashes[i] + hashes[i+1]) 
                  for i in range(0, len(hashes), 2)]
    return hashes[0]
