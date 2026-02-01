"""
VerifyResult - Verification result enumeration.

Reference: Neo.Ledger.VerifyResult
"""

from enum import IntEnum


class VerifyResult(IntEnum):
    """Represents a verifying result of IInventory."""
    
    SUCCEED = 0
    """Verification was successful."""
    
    ALREADY_EXISTS = 1
    """An inventory with the same hash already exists."""
    
    ALREADY_IN_POOL = 2
    """An inventory with the same hash already exists in the memory pool."""
    
    OUT_OF_MEMORY = 3
    """The MemoryPool is full and the transaction cannot be verified."""
    
    UNABLE_TO_VERIFY = 4
    """The previous block has not been received."""
    
    INVALID = 5
    """The inventory is invalid."""
    
    INVALID_SCRIPT = 6
    """The transaction has an invalid script."""
    
    INVALID_ATTRIBUTE = 7
    """The transaction has an invalid attribute."""
    
    INVALID_SIGNATURE = 8
    """The inventory has an invalid signature."""
    
    OVER_SIZE = 9
    """The size of the inventory is not allowed."""
    
    EXPIRED = 10
    """The transaction has expired."""
    
    INSUFFICIENT_FUNDS = 11
    """The transaction failed due to insufficient fees."""
    
    POLICY_FAIL = 12
    """The transaction didn't comply with the policy."""
    
    HAS_CONFLICTS = 13
    """The transaction conflicts with on-chain or mempooled transactions."""
    
    UNKNOWN = 14
    """The inventory failed to verify due to other reasons."""
