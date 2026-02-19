"""Neo N3 Murmur128 hash."""


_C1 = 0x87C37B91114253D5
_C2 = 0x4CF5AD432745937F
_MASK64 = (1 << 64) - 1


def _rotl64(value: int, shift: int) -> int:
    return ((value << shift) & _MASK64) | (value >> (64 - shift))


def _fmix64(value: int) -> int:
    value ^= value >> 33
    value = (value * 0xFF51AFD7ED558CCD) & _MASK64
    value ^= value >> 33
    value = (value * 0xC4CEB9FE1A85EC53) & _MASK64
    value ^= value >> 33
    return value & _MASK64


def murmur128(data: bytes, seed: int = 0) -> bytes:
    """Murmur3 128-bit hash compatible with Neo C# Murmur128."""
    seed_u32 = seed & 0xFFFFFFFF
    h1 = seed_u32
    h2 = seed_u32

    block_count = len(data) // 16
    for block_index in range(block_count):
        start = block_index * 16
        block = data[start : start + 16]
        k1 = int.from_bytes(block[:8], "little")
        k2 = int.from_bytes(block[8:], "little")

        mix1 = (_rotl64((k1 * _C1) & _MASK64, 31) * _C2) & _MASK64
        h1 = (h1 ^ mix1) & _MASK64
        h1 = (_rotl64(h1, 27) + h2) & _MASK64
        h1 = (h1 * 5 + 0x52DCE729) & _MASK64

        mix2 = (_rotl64((k2 * _C2) & _MASK64, 33) * _C1) & _MASK64
        h2 = (h2 ^ mix2) & _MASK64
        h2 = (_rotl64(h2, 31) + h1) & _MASK64
        h2 = (h2 * 5 + 0x38495AB5) & _MASK64

    tail = data[block_count * 16 :].ljust(16, b"\x00")
    if len(data) % 16:
        k1 = int.from_bytes(tail[:8], "little")
        k2 = int.from_bytes(tail[8:], "little")
        h2 ^= (_rotl64((k2 * _C2) & _MASK64, 33) * _C1) & _MASK64
        h2 &= _MASK64
        h1 ^= (_rotl64((k1 * _C1) & _MASK64, 31) * _C2) & _MASK64
        h1 &= _MASK64

    length = len(data)
    h1 ^= length
    h2 ^= length

    h1 = (h1 + h2) & _MASK64
    h2 = (h2 + h1) & _MASK64

    h1 = _fmix64(h1)
    h2 = _fmix64(h2)

    h1 = (h1 + h2) & _MASK64
    h2 = (h2 + h1) & _MASK64

    return h1.to_bytes(8, "little") + h2.to_bytes(8, "little")
