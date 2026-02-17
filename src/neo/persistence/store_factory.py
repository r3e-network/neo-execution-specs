"""Neo N3 Store Factory."""

from __future__ import annotations
from typing import Type

class StoreFactory:
    """Factory for storage providers."""
    
    _providers: dict[str, Type] = {}
    
    @classmethod
    def register(cls, name: str, provider: Type) -> None:
        """Register provider."""
        cls._providers[name] = provider
