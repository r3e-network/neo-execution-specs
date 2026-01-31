"""Execution engine limits."""

from dataclasses import dataclass


@dataclass
class ExecutionEngineLimits:
    """VM execution limits to prevent DoS attacks."""
    
    max_stack_size: int = 2048
    max_item_size: int = 1024 * 1024  # 1 MB
    max_invocation_stack_size: int = 1024
    max_try_nesting_depth: int = 16
    max_shift: int = 256
    
    @classmethod
    def default(cls) -> "ExecutionEngineLimits":
        """Get default limits."""
        return cls()
