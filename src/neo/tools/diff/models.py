"""Data models for diff testing framework."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class ExecutionSource(Enum):
    """Source of execution result."""
    PYTHON_SPEC = "python"
    CSHARP_CLI = "csharp"

@dataclass
class StackValue:
    """Represents a stack value."""
    type: str
    value: Any
    
    def to_dict(self) -> dict:
        return {"type": self.type, "value": self.value}
    
    @classmethod
    def from_dict(cls, data: dict) -> "StackValue":
        return cls(type=data["type"], value=data["value"])
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StackValue):
            return False
        return self.type == other.type and self.value == other.value

@dataclass
class ExecutionResult:
    """Result of executing a test vector."""
    source: ExecutionSource
    state: str  # HALT, FAULT, etc.
    gas_consumed: int = 0
    stack: list[StackValue] = field(default_factory=list)
    state_root: str | None = None
    notifications: list[dict] = field(default_factory=list)
    exception: str | None = None
    raw_response: dict | None = None
    
    def to_dict(self) -> dict:
        return {
            "source": self.source.value,
            "state": self.state,
            "gas_consumed": self.gas_consumed,
            "stack": [s.to_dict() for s in self.stack],
            "state_root": self.state_root,
            "notifications": self.notifications,
            "exception": self.exception,
        }

@dataclass
class TestVector:
    """A test vector for diff testing."""
    name: str
    script: bytes
    description: str = ""
    expected_state: str | None = None
    expected_stack: list[StackValue] | None = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "script": self.script.hex(),
            "description": self.description,
            "expected_state": self.expected_state,
            "expected_stack": [s.to_dict() for s in self.expected_stack] if self.expected_stack else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TestVector":
        expected_stack = None
        if data.get("expected_stack"):
            expected_stack = [StackValue.from_dict(s) for s in data["expected_stack"]]
        expected_state = data.get("expected_state")
        if expected_state is None:
            expected_state = "FAULT" if data.get("error") else "HALT"
        return cls(
            name=data["name"],
            script=bytes.fromhex(data["script"].removeprefix("0x").removeprefix("0X")),
            description=data.get("description", ""),
            expected_state=expected_state,
            expected_stack=expected_stack,
            metadata=data.get("metadata", {}),
        )
