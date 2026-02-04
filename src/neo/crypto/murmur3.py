"""Neo N3 Murmur3 Hash."""


def murmur32(data: bytes, seed: int = 0) -> int:
    """Murmur3 32-bit hash.
    
    Matches Neo C# implementation in Neo.Cryptography.Murmur32.
    """
    c1, c2 = 0xcc9e2d51, 0x1b873593
    h = seed & 0xffffffff
    length = len(data)
    
    # Process 4-byte blocks
    nblocks = length // 4
    for i in range(nblocks):
        k = int.from_bytes(data[i*4:(i+1)*4], 'little')
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = ((h * 5) + 0xe6546b64) & 0xffffffff
    
    # Process tail bytes (remaining bytes that don't form a complete block)
    tail_index = nblocks * 4
    tail_size = length & 3
    k = 0
    if tail_size >= 3:
        k ^= data[tail_index + 2] << 16
    if tail_size >= 2:
        k ^= data[tail_index + 1] << 8
    if tail_size >= 1:
        k ^= data[tail_index]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
    
    # Finalization
    h ^= length
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    h ^= h >> 16
    return h
