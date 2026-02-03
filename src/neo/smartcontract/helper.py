"""Neo N3 Contract Helper."""


def get_contract_hash(sender: bytes, nef_checksum: int, name: str) -> bytes:
    """Calculate contract hash."""
    from neo.crypto.hash import hash160
    data = sender + nef_checksum.to_bytes(4, 'little') + name.encode()
    return hash160(data)
