"""Neo N3 Seek Direction."""

from enum import IntEnum


class SeekDirection(IntEnum):
    """Storage seek direction."""
    FORWARD = 0
    BACKWARD = 1
