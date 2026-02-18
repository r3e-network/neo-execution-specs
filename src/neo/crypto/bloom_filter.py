"""Neo N3 Bloom Filter.

A Bloom filter is a space-efficient probabilistic data structure used to test
whether an element is a member of a set. False positive matches are possible,
but false negatives are not.

Reference: Neo.Cryptography.BloomFilter
"""

import math

from neo.crypto.murmur3 import murmur32


class BloomFilter:
    """Bloom filter for probabilistic set membership testing.

    Args:
        m: Number of bits in the filter
        k: Number of hash functions to use
        seed: Initial seed for hash functions (default 0)
    """

    def __init__(self, m: int, k: int, seed: int = 0):
        """Initialize a new Bloom filter.

        Args:
            m: Number of bits in the filter (will be rounded up to multiple of 8)
            k: Number of hash functions
            seed: Initial seed for the hash functions
        """
        if m <= 0:
            raise ValueError("m must be positive")
        if k <= 0:
            raise ValueError("k must be positive")

        self.m = m
        self.k = k
        self.seed = seed
        self.bits = bytearray((m + 7) // 8)

    def add(self, element: bytes) -> None:
        """Add an element to the Bloom filter.

        Args:
            element: The element to add (as bytes)
        """
        for i in range(self.k):
            # Use different seeds for each hash function
            h = murmur32(element, self.seed + i) % self.m
            byte_index = h // 8
            bit_index = h % 8
            self.bits[byte_index] |= 1 << bit_index

    def check(self, element: bytes) -> bool:
        """Check if an element might be in the set.

        Args:
            element: The element to check (as bytes)

        Returns:
            True if the element might be in the set (possible false positive),
            False if the element is definitely not in the set.
        """
        for i in range(self.k):
            h = murmur32(element, self.seed + i) % self.m
            byte_index = h // 8
            bit_index = h % 8
            if not (self.bits[byte_index] & (1 << bit_index)):
                return False
        return True

    def __contains__(self, element: bytes) -> bool:
        """Support 'in' operator."""
        return self.check(element)

    def clear(self) -> None:
        """Clear all bits in the filter."""
        self.bits = bytearray((self.m + 7) // 8)

    def get_bits(self) -> bytes:
        """Get the raw bit array."""
        return bytes(self.bits)

    def load_bits(self, bits: bytes) -> None:
        """Load bits from a byte array.

        Args:
            bits: The bit array to load (must match filter size)
        """
        if len(bits) != len(self.bits):
            raise ValueError(f"Expected {len(self.bits)} bytes, got {len(bits)}")
        self.bits = bytearray(bits)

    @staticmethod
    def optimal_k(m: int, n: int) -> int:
        """Calculate optimal number of hash functions.

        Args:
            m: Number of bits in the filter
            n: Expected number of elements

        Returns:
            Optimal number of hash functions
        """
        if n <= 0:
            return 1
        return max(1, round((m / n) * math.log(2)))

    @staticmethod
    def optimal_m(n: int, p: float) -> int:
        """Calculate optimal filter size for desired false positive rate.

        Args:
            n: Expected number of elements
            p: Desired false positive probability (0 < p < 1)

        Returns:
            Optimal number of bits
        """
        if n <= 0 or p <= 0 or p >= 1:
            raise ValueError("Invalid parameters")
        return int(-n * math.log(p) / (math.log(2) ** 2))

    @property
    def size(self) -> int:
        """Return the size of the filter in bits."""
        return self.m

    @property
    def hash_count(self) -> int:
        """Return the number of hash functions."""
        return self.k
