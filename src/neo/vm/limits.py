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
    max_try_nesting_depth: int = 16
    
    def assert_max_item_size(self, size: int) -> None:
        """Assert that item size is within limits."""
        if size > self.max_item_size:
            raise Exception(f"Item size {size} exceeds maximum {self.max_item_size}")
    
    def assert_max_stack_size(self, size: int) -> None:
        """Assert that stack size is within limits."""
        if size > self.max_stack_size:
            raise Exception(f"Stack size {size} exceeds maximum {self.max_stack_size}")
    
    def assert_shift(self, shift: int) -> None:
        """Assert that shift amount is valid."""
        if shift < 0 or shift > 256:
            raise Exception(f"Shift amount {shift} out of range")
