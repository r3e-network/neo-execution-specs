"""Native contract base class."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from neo.types import UInt160


@dataclass
class NativeContract(ABC):
    """Base class for native contracts."""
    
    id: int
    name: str
    
    @property
    @abstractmethod
    def hash(self) -> UInt160:
        """Contract script hash."""
        ...
