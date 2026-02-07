"""Neo N3 Seek Direction."""

from enum import IntEnum


class SeekDirection(IntEnum):
    """Storage seek direction.

    Matches C# Neo.IO.Storage.SeekDirection:
      Forward  =  1
      Backward = -1
    """
    FORWARD = 1
    BACKWARD = -1
