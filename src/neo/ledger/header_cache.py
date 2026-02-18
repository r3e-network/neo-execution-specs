"""
HeaderCache - Block header caching.

Reference: Neo.Ledger.HeaderCache
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from threading import RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.network.payloads.header import Header

class HeaderCache:
    """Cache for block headers not yet received."""

    MAX_HEADERS = 10_000

    def __init__(self) -> None:
        self._headers: deque[Header] = deque()
        self._lock = RLock()

    def __getitem__(self, index: int) -> Header | None:
        """Get header at index."""
        with self._lock:
            if not self._headers:
                return None
            first_index = self._headers[0].index
            if index < first_index:
                return None
            offset = index - first_index
            if offset >= len(self._headers):
                return None
            return self._headers[offset]

    @property
    def count(self) -> int:
        """Get number of headers in cache."""
        with self._lock:
            return len(self._headers)

    @property
    def full(self) -> bool:
        """Check if cache is full."""
        return self.count >= self.MAX_HEADERS

    @property
    def last(self) -> Header | None:
        """Get last header in cache."""
        with self._lock:
            return self._headers[-1] if self._headers else None

    def add(self, header: Header) -> bool:
        """Add a header to the cache."""
        with self._lock:
            if len(self._headers) >= self.MAX_HEADERS:
                return False
            self._headers.append(header)
            return True

    def try_remove_first(self) -> Header | None:
        """Remove and return the first header (O(1) with deque)."""
        with self._lock:
            return self._headers.popleft() if self._headers else None

    def __iter__(self) -> Iterator[Header]:
        """Iterate over headers."""
        with self._lock:
            yield from self._headers

    def __len__(self) -> int:
        """Get number of headers."""
        return self.count
