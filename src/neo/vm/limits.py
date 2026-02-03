"""Neo N3 VM Limits."""

from dataclasses import dataclass


# Execution limits
MAX_STACK_SIZE = 2048
MAX_ITEM_SIZE = 1024 * 1024
MAX_INVOCATION_STACK_SIZE = 1024
MAX_SCRIPT_LENGTH = 512 * 1024


@dataclass
class ExecutionEngineLimits:
    """VM execution limits."""
    max_stack_size: int = MAX_STACK_SIZE
    max_item_size: int = MAX_ITEM_SIZE
    max_invocation_stack_size: int = MAX_INVOCATION_STACK_SIZE
    max_script_length: int = MAX_SCRIPT_LENGTH
