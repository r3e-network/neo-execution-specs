"""ContractParameterType - Types for contract parameters."""

from enum import IntEnum


class ContractParameterType(IntEnum):
    """Parameter types for smart contract methods."""
    
    ANY = 0x00
    BOOLEAN = 0x10
    INTEGER = 0x11
    BYTE_ARRAY = 0x12
    STRING = 0x13
    HASH160 = 0x14
    HASH256 = 0x15
    PUBLIC_KEY = 0x16
    SIGNATURE = 0x17
    ARRAY = 0x20
    MAP = 0x22
    INTEROP_INTERFACE = 0x30
    VOID = 0xFF
