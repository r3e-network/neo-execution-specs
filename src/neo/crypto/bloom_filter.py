"""Neo N3 Bloom Filter."""

import math


class BloomFilter:
    """Bloom filter."""
    
    def __init__(self, m: int, k: int):
        self.bits = bytearray(m // 8)
        self.k = k
        self.m = m
