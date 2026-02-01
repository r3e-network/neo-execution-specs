"""Stack manipulation instructions for NeoVM.

This module implements all stack manipulation opcodes (0x43-0x55):
- DEPTH: Push stack depth
- DROP, NIP, XDROP, CLEAR: Remove items
- DUP, OVER, PICK, TUCK: Copy items
- SWAP, ROT, ROLL: Reorder items
- REVERSE3, REVERSE4, REVERSEN: Reverse items
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Integer

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def depth(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push the number of items on the stack.
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(Integer(len(engine.current_context.evaluation_stack)))


def drop(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Remove the top item from the stack.
    
    Example: a b c -> a b
    
    Push: 0 items
    Pop: 1 item
    """
    engine.pop()


def nip(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Remove the second-to-top item from the stack.
    
    Example: a b c -> a c
    
    Push: 0 items
    Pop: 1 item
    """
    engine.current_context.evaluation_stack.remove(1)


def xdrop(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Remove the item n positions back from the top.
    
    Pop n from stack, then remove item at position n.
    
    Push: 0 items
    Pop: n+1 items
    """
    n = int(engine.pop().get_integer())
    if n < 0:
        raise Exception(f"The negative value {n} is invalid for XDROP.")
    engine.current_context.evaluation_stack.remove(n)


def clear(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Clear all items from the stack.
    
    Push: 0 items
    Pop: all items
    """
    engine.current_context.evaluation_stack.clear()


def dup(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Duplicate the top item on the stack.
    
    Example: a b c -> a b c c
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(engine.peek())


def over(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Copy the second-to-top item to the top.
    
    Example: a b c -> a b c b
    
    Push: 1 item
    Pop: 0 items
    """
    engine.push(engine.peek(1))


def pick(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Copy the item n positions back to the top.
    
    Example: a b c d 2 -> a b c d b
    
    Push: 1 item
    Pop: 1 item (the index)
    """
    n = int(engine.pop().get_integer())
    if n < 0:
        raise Exception(f"The negative value {n} is invalid for PICK.")
    engine.push(engine.peek(n))


def tuck(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Copy top item and insert before second-to-top.
    
    Example: a b c -> a c b c
    
    Push: 1 item
    Pop: 0 items
    """
    engine.current_context.evaluation_stack.insert(2, engine.peek())


def swap(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Swap the top two items on the stack.
    
    Example: a b -> b a
    
    Push: 0 items
    Pop: 0 items
    """
    engine.current_context.evaluation_stack.swap(0, 1)


def rot(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Left rotate the top three items.
    
    Example: a b c -> b c a
    
    Push: 0 items
    Pop: 0 items
    """
    stack = engine.current_context.evaluation_stack
    stack.swap(1, 2)
    stack.swap(0, 1)


def roll(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Move item n positions back to the top.
    
    Example: a b c d 2 -> a c d b
    
    Push: 1 item
    Pop: 1 item (the index)
    """
    n = int(engine.pop().get_integer())
    if n < 0:
        raise Exception(f"The negative value {n} is invalid for ROLL.")
    if n == 0:
        return
    item = engine.current_context.evaluation_stack.remove(n)
    engine.push(item)


def reverse3(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Reverse the order of the top 3 items.
    
    Example: a b c -> c b a
    
    Push: 0 items
    Pop: 0 items
    """
    engine.current_context.evaluation_stack.reverse(3)


def reverse4(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Reverse the order of the top 4 items.
    
    Example: a b c d -> d c b a
    
    Push: 0 items
    Pop: 0 items
    """
    engine.current_context.evaluation_stack.reverse(4)


def reversen(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Reverse the order of the top n items.
    
    Example: a b c d 3 -> a d c b
    
    Push: 0 items
    Pop: 1 item (the count)
    """
    n = int(engine.pop().get_integer())
    engine.current_context.evaluation_stack.reverse(n)
