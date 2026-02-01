"""
Murmur hash implementation.

Reference: Neo.Cryptography.Murmur32
"""


def murmur32(data: bytes, seed: int = 0) -> int:
    """Compute Murmur3 32-bit hash."""
    c1 = 0xcc9e2d51
    c2 = 0x1b873593
    h1 = seed & 0xffffffff
    length = len(data)
    
    # Process 4-byte chunks
    for i in range(0, length - 3, 4):
        k1 = int.from_bytes(data[i:i+4], 'little')
        k1 = (k1 * c1) & 0xffffffff
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xffffffff
        k1 = (k1 * c2) & 0xffffffff
        h1 ^= k1
        h1 = ((h1 << 13) | (h1 >> 19)) & 0xffffffff
        h1 = ((h1 * 5) + 0xe6546b64) & 0xffffffff
    
    # Handle remaining bytes
    tail_index = (length // 4) * 4
    k1 = 0
    tail_size = length & 3
    
    if tail_size >= 3:
        k1 ^= data[tail_index + 2] << 16
    if tail_size >= 2:
        k1 ^= data[tail_index + 1] << 8
    if tail_size >= 1:
        k1 ^= data[tail_index]
        k1 = (k1 * c1) & 0xffffffff
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xffffffff
        k1 = (k1 * c2) & 0xffffffff
        h1 ^= k1
    
    # Finalization
    h1 ^= length
    h1 ^= h1 >> 16
    h1 = (h1 * 0x85ebca6b) & 0xffffffff
    h1 ^= h1 >> 13
    h1 = (h1 * 0xc2b2ae35) & 0xffffffff
    h1 ^= h1 >> 16
    
    return h1
