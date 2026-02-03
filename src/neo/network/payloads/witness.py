"""Neo N3 Witness."""

from dataclasses import dataclass


def _get_var_size(value: int) -> int:
    """Get variable int size."""
    if value < 0xFD:
        return 1
    elif value <= 0xFFFF:
        return 3
    elif value <= 0xFFFFFFFF:
        return 5
    return 9


@dataclass
class Witness:
    """Transaction witness."""
    invocation_script: bytes = b""
    verification_script: bytes = b""
    
    @classmethod
    def empty(cls) -> "Witness":
        """Create empty witness."""
        return cls()
    
    @property
    def size(self) -> int:
        """Get serialized size."""
        return (_get_var_size(len(self.invocation_script)) + 
                len(self.invocation_script) +
                _get_var_size(len(self.verification_script)) + 
                len(self.verification_script))
    
    @property
    def script_hash(self) -> bytes:
        """Get verification script hash."""
        from neo.crypto.hash import hash160
        return hash160(self.verification_script)
