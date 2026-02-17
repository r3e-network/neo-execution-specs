"""Contract ABI definitions."""

from __future__ import annotations
from dataclasses import dataclass, field

from enum import IntEnum

class ContractParameterType(IntEnum):
    """Parameter types."""
    ANY = 0x00
    BOOLEAN = 0x10
    INTEGER = 0x11
    BYTEARRAY = 0x12
    STRING = 0x13
    HASH160 = 0x14
    HASH256 = 0x15
    PUBLICKEY = 0x16
    SIGNATURE = 0x17
    ARRAY = 0x20
    MAP = 0x22
    INTEROP = 0x30
    VOID = 0xFF

@dataclass
class ContractParameterDefinition:
    """Parameter definition."""
    name: str
    type: ContractParameterType

@dataclass
class ContractMethodDescriptor:
    """Method descriptor."""
    name: str
    parameters: list[ContractParameterDefinition] = field(default_factory=list)
    return_type: ContractParameterType = ContractParameterType.VOID
    offset: int = 0
    safe: bool = False

@dataclass
class ContractEventDescriptor:
    """Event descriptor."""
    name: str
    parameters: list[ContractParameterDefinition] = field(default_factory=list)

@dataclass
class ContractAbi:
    """Contract ABI."""
    methods: list[ContractMethodDescriptor] = field(default_factory=list)
    events: list[ContractEventDescriptor] = field(default_factory=list)
