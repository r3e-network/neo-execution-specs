"""Control flow instructions for NeoVM.

This module implements all control flow opcodes (0x21-0x41):
- NOP: No operation
- JMP variants: Unconditional and conditional jumps
- CALL variants: Function calls
- ABORT, ASSERT: Execution control
- TRY/CATCH/FINALLY: Exception handling
- RET: Return from function
- SYSCALL: System calls
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.vm.types import Pointer

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def nop(engine: ExecutionEngine, instruction: Instruction) -> None:
    """No operation - does nothing.
    
    Used for padding or as a placeholder.
    """
    pass


def jmp(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Unconditional jump (1-byte offset).
    
    Operand: 1 byte signed offset
    """
    offset = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.execute_jump_offset(offset)


def jmp_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Unconditional jump (4-byte offset).
    
    Operand: 4 byte signed offset
    """
    offset = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.execute_jump_offset(offset)


def jmpif(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if top of stack is true (1-byte offset).
    
    Pop: 1 item
    """
    if engine.pop().get_boolean():
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpif_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if top of stack is true (4-byte offset).
    
    Pop: 1 item
    """
    if engine.pop().get_boolean():
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpifnot(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if top of stack is false (1-byte offset).
    
    Pop: 1 item
    """
    if not engine.pop().get_boolean():
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpifnot_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if top of stack is false (4-byte offset).
    
    Pop: 1 item
    """
    if not engine.pop().get_boolean():
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpeq(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if two integers are equal (1-byte offset).
    
    Pop: 2 items
    """
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 == x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpeq_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if two integers are equal (4-byte offset).
    
    Pop: 2 items
    """
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 == x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpne(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if two integers are not equal (1-byte offset).
    
    Pop: 2 items
    """
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 != x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpne_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if two integers are not equal (4-byte offset).
    
    Pop: 2 items
    """
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 != x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpgt(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer > second (1-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 > x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpgt_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer > second (4-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 > x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpge(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer >= second (1-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 >= x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmpge_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer >= second (4-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 >= x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmplt(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer < second (1-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 < x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmplt_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer < second (4-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 < x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmple(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer <= second (1-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 <= x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def jmple_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Jump if first integer <= second (4-byte offset)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x1 <= x2:
        offset = int.from_bytes(instruction.operand, 'little', signed=True)
        engine.execute_jump_offset(offset)


def call(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Call function at offset (1-byte offset)."""
    offset = int.from_bytes(instruction.operand, 'little', signed=True)
    position = engine.current_context.ip + offset
    engine.execute_call(position)


def call_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Call function at offset (4-byte offset)."""
    offset = int.from_bytes(instruction.operand, 'little', signed=True)
    position = engine.current_context.ip + offset
    engine.execute_call(position)


def calla(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Call function at pointer address from stack."""
    ptr = engine.pop()
    if not isinstance(ptr, Pointer):
        raise Exception("Expected Pointer on stack for CALLA")
    if ptr.script is not engine.current_context.script:
        raise Exception("Pointers can't be shared between scripts")
    engine.execute_call(ptr.position)


def callt(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Call function by token (for contract calls).
    
    CALLT uses a 2-byte token index to reference a MethodToken in the NEF file.
    The token contains the contract hash, method name, parameter count,
    return value flag, and call flags.
    
    This instruction requires a token_handler to be set on the engine.
    In ApplicationEngine, this handler resolves the token and calls the contract.
    """
    token_index = int.from_bytes(instruction.operand, 'little', signed=False)
    
    # Check if engine has a token handler
    if hasattr(engine, 'token_handler') and engine.token_handler is not None:
        engine.token_handler(engine, token_index)
    else:
        raise Exception(f"CALLT requires token handler. Token index: {token_index}")


def abort(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Abort execution immediately (cannot be caught)."""
    raise Exception("ABORT is executed.")


def assert_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Assert top of stack is true, else fault."""
    if not engine.pop().get_boolean():
        raise Exception("ASSERT is executed with false result.")


def throw(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Throw exception from top of stack."""
    ex = engine.pop()
    engine.execute_throw(ex)


def try_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Begin try block (1-byte offsets)."""
    catch_offset = instruction.operand[0]
    if catch_offset >= 128:
        catch_offset -= 256
    finally_offset = instruction.operand[1]
    if finally_offset >= 128:
        finally_offset -= 256
    engine.execute_try(catch_offset, finally_offset)


def try_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Begin try block (4-byte offsets)."""
    catch_offset = int.from_bytes(instruction.operand[0:4], 'little', signed=True)
    finally_offset = int.from_bytes(instruction.operand[4:8], 'little', signed=True)
    engine.execute_try(catch_offset, finally_offset)


def endtry(engine: ExecutionEngine, instruction: Instruction) -> None:
    """End try block (1-byte offset)."""
    offset = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.execute_endtry(offset)


def endtry_l(engine: ExecutionEngine, instruction: Instruction) -> None:
    """End try block (4-byte offset)."""
    offset = int.from_bytes(instruction.operand, 'little', signed=True)
    engine.execute_endtry(offset)


def endfinally(engine: ExecutionEngine, instruction: Instruction) -> None:
    """End finally block."""
    engine.execute_endfinally()


def ret(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Return from current method."""
    engine.execute_ret()


def syscall(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Call system service by hash."""
    hash_value = int.from_bytes(instruction.operand, 'little', signed=False)
    if hasattr(engine, 'syscall_handler') and engine.syscall_handler is not None:
        engine.syscall_handler(engine, hash_value)
    else:
        raise Exception(f"Syscall not found: {hash_value}")
