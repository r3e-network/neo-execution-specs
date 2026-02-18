"""Neo N3 VM Limits."""

from dataclasses import dataclass

from neo.exceptions import InvalidOperationException

# Execution limits
MAX_STACK_SIZE = 2048
MAX_ITEM_SIZE = 65535 * 2  # 131070, matches C# ushort.MaxValue * 2
MAX_INVOCATION_STACK_SIZE = 1024
MAX_SCRIPT_LENGTH = 512 * 1024
MAX_SHIFT = 256  # Maximum bits for SHL/SHR
MAX_COMPARABLE_SIZE = 65536  # Maximum size for comparison operations


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
            raise InvalidOperationException(f"Item size {size} exceeds maximum {self.max_item_size}")

    def assert_max_stack_size(self, size: int) -> None:
        """Assert that stack size is within limits."""
        if size > self.max_stack_size:
            raise InvalidOperationException(f"Stack size {size} exceeds maximum {self.max_stack_size}")

    def assert_shift(self, shift: int) -> None:
        """Assert that shift amount is valid."""
        if shift < 0 or shift > MAX_SHIFT:
            raise InvalidOperationException(f"Shift amount {shift} out of range")
