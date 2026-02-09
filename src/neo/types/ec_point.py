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
        """Decode from bytes (secp256r1)."""
        from neo.crypto.ecc.curve import SECP256R1
        from neo.crypto.ecc.point import ECPoint as CryptoPoint

        if len(data) == 1 and data[0] == 0x00:
            return cls.infinity()

        if len(data) == 33 and data[0] in (0x02, 0x03):
            x = int.from_bytes(data[1:], 'big')
            is_odd = data[0] == 0x03
            y = CryptoPoint._decompress_y(x, is_odd, SECP256R1)
            return cls(x=x, y=y)

        if len(data) == 65 and data[0] == 0x04:
            x = int.from_bytes(data[1:33], 'big')
            y = int.from_bytes(data[33:], 'big')
            return cls(x=x, y=y)

        raise ValueError(f"Invalid EC point encoding ({len(data)} bytes)")
    
    def encode(self, compressed: bool = True) -> bytes:
        """Encode to bytes."""
        if compressed:
            prefix = 0x02 if self.y % 2 == 0 else 0x03
            return bytes([prefix]) + self.x.to_bytes(32, 'big')
        return bytes([0x04]) + self.x.to_bytes(32, 'big') + self.y.to_bytes(32, 'big')
