"""Neo N3 Store Factory."""

from typing import Dict, Type


class StoreFactory:
    """Factory for storage providers."""
    
    _providers: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, name: str, provider: Type) -> None:
        """Register provider."""
        cls._providers[name] = provider
