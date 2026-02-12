"""Exception handling context for NeoVM.

This module implements the exception handling state machine used by
TRY/CATCH/FINALLY blocks in the Neo Virtual Machine.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional

from neo.exceptions import InvalidOperationException


class ExceptionHandlingState(IntEnum):
    """Indicates the state of the ExceptionHandlingContext."""
    TRY = 0      # The try block is being executed
    CATCH = 1    # The catch block is being executed
    FINALLY = 2  # The finally block is being executed


@dataclass
class ExceptionHandlingContext:
    """Represents the context used for exception handling.
    
    This class tracks the state of a try-catch-finally block during execution.
    
    Attributes:
        catch_pointer: Position of the catch block (-1 if none).
        finally_pointer: Position of the finally block (-1 if none).
        end_pointer: End position of the try-catch-finally block.
        state: Current state of exception handling.
    """
    catch_pointer: int
    finally_pointer: int
    end_pointer: int = -1
    state: ExceptionHandlingState = ExceptionHandlingState.TRY
    
    @property
    def has_catch(self) -> bool:
        """Check if this context has a catch block."""
        return self.catch_pointer >= 0
    
    @property
    def has_finally(self) -> bool:
        """Check if this context has a finally block."""
        return self.finally_pointer >= 0


class TryStack:
    """Stack of exception handling contexts.
    
    Manages nested try-catch-finally blocks.
    """
    
    def __init__(self) -> None:
        self._stack: List[ExceptionHandlingContext] = []
    
    def push(self, context: ExceptionHandlingContext) -> None:
        """Push a new exception handling context."""
        self._stack.append(context)
    
    def pop(self) -> ExceptionHandlingContext:
        """Pop and return the top exception handling context."""
        if not self._stack:
            raise InvalidOperationException("The corresponding TRY block cannot be found.")
        return self._stack.pop()
    
    def peek(self) -> ExceptionHandlingContext:
        """Peek at the top exception handling context without removing it."""
        if not self._stack:
            raise InvalidOperationException("The corresponding TRY block cannot be found.")
        return self._stack[-1]
    
    def try_peek(self) -> tuple[bool, Optional[ExceptionHandlingContext]]:
        """Try to peek at the top context, returning (success, context)."""
        if not self._stack:
            return False, None
        return True, self._stack[-1]
    
    def try_pop(self) -> tuple[bool, Optional[ExceptionHandlingContext]]:
        """Try to pop the top context, returning (success, context)."""
        if not self._stack:
            return False, None
        return True, self._stack.pop()
    
    def __len__(self) -> int:
        return len(self._stack)
    
    def __bool__(self) -> bool:
        return bool(self._stack)
