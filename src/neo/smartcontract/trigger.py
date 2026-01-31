"""Trigger types for contract execution."""

from enum import IntEnum


class TriggerType(IntEnum):
    """Contract execution trigger types."""
    
    SYSTEM = 0x01
    VERIFICATION = 0x20
    APPLICATION = 0x40
    ALL = SYSTEM | VERIFICATION | APPLICATION
