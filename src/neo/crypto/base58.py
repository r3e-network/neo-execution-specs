"""
Base58 encoding/decoding.

Reference: Neo.Cryptography.Base58
"""

ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def encode(data: bytes) -> str:
    """Encode bytes to Base58."""
    n = int.from_bytes(data, 'big')
    result = []
    while n > 0:
        n, r = divmod(n, 58)
        result.append(ALPHABET[r])
    
    # Handle leading zeros
    for b in data:
        if b == 0:
            result.append(ALPHABET[0])
        else:
            break
    
    return bytes(reversed(result)).decode('ascii')


def decode(s: str) -> bytes:
    """Decode Base58 string to bytes."""
    n = 0
    for c in s.encode('ascii'):
        n = n * 58 + ALPHABET.index(c)
    
    # Calculate byte length
    length = (n.bit_length() + 7) // 8
    
    # Handle leading '1's (zeros)
    leading_zeros = 0
    for c in s:
        if c == '1':
            leading_zeros += 1
        else:
            break
    
    result = n.to_bytes(length, 'big') if n else b''
    return b'\x00' * leading_zeros + result


def base58_check_encode(data: bytes) -> str:
    """Encode with checksum."""
    from neo.crypto.hash import hash256
    checksum = hash256(data)[:4]
    return encode(data + checksum)


def base58_check_decode(s: str) -> bytes:
    """Decode and verify checksum."""
    from neo.crypto.hash import hash256
    data = decode(s)
    payload, checksum = data[:-4], data[-4:]
    if hash256(payload)[:4] != checksum:
        raise ValueError("Invalid checksum")
    return payload
