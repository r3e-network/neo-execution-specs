"""Neo N3 Track State."""

from enum import IntEnum


class TrackState(IntEnum):
    """Data tracking state."""
    NONE = 0
    ADDED = 1
    CHANGED = 2
    DELETED = 3
