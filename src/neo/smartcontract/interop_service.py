"""Interop service for syscall registration and dispatch."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, TYPE_CHECKING
import hashlib

from neo.smartcontract.call_flags import CallFlags

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


@dataclass
class InteropDescriptor:
    """Syscall descriptor."""
    name: str
    handler: Callable[[ApplicationEngine], None]
    price: int
    required_flags: CallFlags


def get_interop_hash(name: str) -> int:
    """Get syscall hash from name."""
    data = name.encode('ascii')
    hash_bytes = hashlib.sha256(data).digest()[:4]
    return int.from_bytes(hash_bytes, 'little')


# Syscall registry
_syscalls: Dict[int, InteropDescriptor] = {}


def register_syscall(
    name: str,
    handler: Callable,
    price: int = 0,
    flags: CallFlags = CallFlags.NONE
) -> None:
    """Register a syscall."""
    hash_val = get_interop_hash(name)
    _syscalls[hash_val] = InteropDescriptor(name, handler, price, flags)


def get_syscall(hash_val: int) -> InteropDescriptor | None:
    """Get syscall by hash."""
    return _syscalls.get(hash_val)


def invoke_syscall(engine: "ApplicationEngine", hash_val: int) -> None:
    """Invoke a syscall by hash."""
    descriptor = get_syscall(hash_val)
    if descriptor is None:
        raise ValueError(f"Unknown syscall: {hash_val:#x}")
    
    # Charge gas
    engine.add_gas(descriptor.price)
    
    # Invoke handler
    descriptor.handler(engine)
