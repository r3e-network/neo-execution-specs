"""Neo N3 Store Factory."""

from __future__ import annotations


class StoreFactory:
    """Factory for storage providers."""

    _providers: dict[str, type] = {}

    @classmethod
    def register(cls, name: str, provider: type) -> None:
        """Register provider."""
        cls._providers[name] = provider
