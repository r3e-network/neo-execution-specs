"""Neo N3 ECPoint type."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ECPoint:
    """Elliptic curve point."""
    x: int
    y: int
    curve: str = "secp256r1"
    
    @classmethod
    def infinity(cls) -> "ECPoint":
        return cls(0, 0)
    
    @classmethod
    def decode(cls, data: bytes) -> "ECPoint":
        """Decode from bytes."""
        if len(data) == 33:
            # Compressed
            prefix = data[0]
            x = int.from_bytes(data[1:], 'big')
            # Decompress y
            return cls(x=x, y=0)  # Simplified
        elif len(data) == 65:
            # Uncompressed
            x = int.from_bytes(data[1:33], 'big')
            y = int.from_bytes(data[33:], 'big')
            return cls(x=x, y=y)
        raise ValueError("Invalid point")
    
    def encode(self, compressed: bool = True) -> bytes:
        """Encode to bytes."""
        if compressed:
            prefix = 0x02 if self.y % 2 == 0 else 0x03
            return bytes([prefix]) + self.x.to_bytes(32, 'big')
        return bytes([0x04]) + self.x.to_bytes(32, 'big') + self.y.to_bytes(32, 'big')
