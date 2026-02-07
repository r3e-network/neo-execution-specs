"""Interop service for syscall registration and dispatch."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, TYPE_CHECKING
import hashlib

from neo.smartcontract.call_flags import CallFlags
from neo.hardfork import Hardfork

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


@dataclass
class InteropDescriptor:
    """Syscall descriptor."""
    name: str
    handler: Callable[[ApplicationEngine], None]
    price: int
    required_flags: CallFlags
    hardfork: Hardfork | None = None


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
    flags: CallFlags = CallFlags.NONE,
    hardfork: Hardfork | None = None,
) -> None:
    """Register a syscall."""
    hash_val = get_interop_hash(name)
    _syscalls[hash_val] = InteropDescriptor(name, handler, price, flags, hardfork)


def get_syscall(hash_val: int) -> InteropDescriptor | None:
    """Get syscall by hash."""
    return _syscalls.get(hash_val)


def _is_hardfork_enabled(engine: "ApplicationEngine", hardfork: Hardfork) -> bool:
    """Check hardfork activation for syscall gating.

    Matches Neo behavior:
    - If no protocol settings are present, hardfork-gated syscalls are disabled.
    - If no persisting block is available, hardfork is considered enabled when configured.
    - Otherwise, evaluate against the current persisting block index.
    """
    settings = getattr(engine, "protocol_settings", None)
    if settings is None:
        return False

    snapshot = getattr(engine, "snapshot", None)
    block = getattr(snapshot, "persisting_block", None) if snapshot is not None else None

    if block is None:
        hardforks = getattr(settings, "hardforks", {})
        return hardfork in hardforks

    if not hasattr(settings, "is_hardfork_enabled"):
        return False

    index = int(getattr(block, "index", 0))
    return bool(settings.is_hardfork_enabled(hardfork, index))


def invoke_syscall(engine: "ApplicationEngine", hash_val: int) -> None:
    """Invoke a syscall by hash."""
    descriptor = get_syscall(hash_val)
    if descriptor is None:
        raise ValueError(f"Unknown syscall: {hash_val:#x}")

    if descriptor.hardfork is not None and not _is_hardfork_enabled(engine, descriptor.hardfork):
        raise KeyError(f"Syscall not active for hardfork: {descriptor.name}")

    current_flags = getattr(engine, "_current_call_flags", CallFlags.NONE)
    current_flags = CallFlags(int(current_flags))
    if (current_flags & descriptor.required_flags) != descriptor.required_flags:
        raise PermissionError(
            f"Cannot call syscall {descriptor.name} with call flags {current_flags}"
        )

    # Charge gas
    engine.add_gas(descriptor.price)
    
    # Invoke handler
    descriptor.handler(engine)
