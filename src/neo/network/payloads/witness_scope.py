"""
WitnessScope - Defines the scope of a witness.

Reference: Neo.Network.P2P.Payloads.WitnessScope
"""

from enum import IntFlag


class WitnessScope(IntFlag):
    """
    Represents the scope of a witness.
    """
    
    # No contract was witnessed. Only sign the transaction.
    NONE = 0x00
    
    # Allow the witness in all contexts (global).
    # This cannot be combined with other flags.
    CALLED_BY_ENTRY = 0x01
    
    # Custom contract hashes are allowed.
    CUSTOM_CONTRACTS = 0x10
    
    # Custom groups are allowed.
    CUSTOM_GROUPS = 0x20
    
    # Witness rules are allowed.
    WITNESS_RULES = 0x40
    
    # Global scope (all contracts).
    GLOBAL = 0x80
