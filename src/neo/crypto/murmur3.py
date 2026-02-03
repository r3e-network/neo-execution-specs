"""Neo N3 Murmur3 Hash."""


def murmur32(data: bytes, seed: int = 0) -> int:
    """Murmur3 32-bit hash."""
    c1, c2 = 0xcc9e2d51, 0x1b873593
    h = seed
    for i in range(0, len(data) - 3, 4):
        k = int.from_bytes(data[i:i+4], 'little')
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = ((h * 5) + 0xe6546b64) & 0xffffffff
    h ^= len(data)
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    h ^= h >> 16
    return h
