"""BigInteger implementation for Neo."""

from __future__ import annotations


class BigInteger(int):
    """Arbitrary precision integer."""
    
    MAX_SIZE = 32  # Maximum bytes
    
    def __new__(cls, value: int = 0) -> BigInteger:
        return super().__new__(cls, value)
    
    def to_bytes_le(self) -> bytes:
        """Convert to little-endian bytes."""
        if self == 0:
            return b"\x00"
        
        negative = self < 0
        value = abs(int(self))
        
        result = []
        while value > 0:
            result.append(value & 0xFF)
            value >>= 8
        
        # Handle sign
        if negative:
            # Two's complement
            carry = 1
            for i in range(len(result)):
                result[i] = (~result[i] & 0xFF) + carry
                carry = result[i] >> 8
                result[i] &= 0xFF
            if result[-1] & 0x80 == 0:
                result.append(0xFF)
        elif result[-1] & 0x80:
            result.append(0x00)
        
        return bytes(result)
    
    @classmethod
    def from_bytes_le(cls, data: bytes) -> BigInteger:
        """Create from little-endian bytes."""
        if len(data) == 0:
            return cls(0)
        
        negative = data[-1] & 0x80 != 0
        
        if negative:
            # Two's complement
            data = bytearray(data)
            carry = 1
            for i in range(len(data)):
                data[i] = (~data[i] & 0xFF) + carry
                carry = data[i] >> 8
                data[i] &= 0xFF
        
        value = int.from_bytes(data, "little")
        return cls(-value if negative else value)
