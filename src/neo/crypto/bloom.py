"""
Bloom Filter implementation.

Reference: Neo.Cryptography.BloomFilter
"""

from neo.crypto.murmur import murmur32


class BloomFilter:
    """Bloom filter for probabilistic set membership."""
    
    def __init__(self, m: int, k: int, seed: int = 0):
        self.bits = bytearray((m + 7) // 8)
        self.m = m
        self.k = k
        self.seed = seed
    
    def add(self, element: bytes) -> None:
        """Add element to filter."""
        for i in range(self.k):
            h = murmur32(element, self.seed + i) % self.m
            self.bits[h >> 3] |= (1 << (h & 7))
    
    def contains(self, element: bytes) -> bool:
        """Check if element might be in filter."""
        for i in range(self.k):
            h = murmur32(element, self.seed + i) % self.m
            if not (self.bits[h >> 3] & (1 << (h & 7))):
                return False
        return True
