"""Numeric instructions for NeoVM.

This module implements all numeric opcodes (0x99-0xBB):
- SIGN, ABS, NEGATE: Unary operations
- INC, DEC: Increment/decrement
- ADD, SUB, MUL, DIV, MOD: Basic arithmetic
- POW, SQRT, MODMUL, MODPOW: Advanced math
- SHL, SHR: Bit shifting
- NOT, BOOLAND, BOOLOR, NZ: Boolean operations
- Comparison: NUMEQUAL, NUMNOTEQUAL, LT, LE, GT, GE, MIN, MAX, WITHIN
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import math

from neo.vm.types import Integer, Boolean

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def sign(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push sign of integer (-1, 0, or 1)."""
    x = engine.pop().get_integer()
    if x > 0:
        engine.push(Integer(1))
    elif x < 0:
        engine.push(Integer(-1))
    else:
        engine.push(Integer(0))


def abs_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push absolute value of integer."""
    x = engine.pop().get_integer()
    engine.push(Integer(abs(x)))


def negate(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push negation of integer."""
    x = engine.pop().get_integer()
    engine.push(Integer(-x))


def inc(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Increment integer by 1."""
    x = engine.pop().get_integer()
    engine.push(Integer(x + 1))


def dec(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Decrement integer by 1."""
    x = engine.pop().get_integer()
    engine.push(Integer(x - 1))


def add(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Add two integers."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(x1 + x2))


def sub(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Subtract two integers."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(x1 - x2))


def mul(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Multiply two integers."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(x1 * x2))


def div(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Divide two integers (floor division)."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x2 == 0:
        raise Exception("Division by zero")
    # Python's // does floor division, C# does truncation
    # For negative numbers, we need truncation toward zero
    if (x1 < 0) != (x2 < 0) and x1 % x2 != 0:
        result = x1 // x2 + 1
    else:
        result = x1 // x2
    engine.push(Integer(result))


def mod(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Modulo of two integers."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    if x2 == 0:
        raise Exception("Division by zero")
    # C# remainder has same sign as dividend
    result = x1 % x2
    if result != 0 and (x1 < 0) != (x2 < 0):
        result = result - x2
    engine.push(Integer(result))


def pow_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Raise integer to power."""
    exponent = int(engine.pop().get_integer())
    engine.limits.assert_shift(exponent)
    value = engine.pop().get_integer()
    engine.push(Integer(value ** exponent))


def sqrt(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Integer square root."""
    x = engine.pop().get_integer()
    if x < 0:
        raise Exception("Cannot compute square root of negative number")
    engine.push(Integer(int(math.isqrt(x))))


def modmul(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Modular multiplication: (x1 * x2) % modulus."""
    modulus = engine.pop().get_integer()
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer((x1 * x2) % modulus))


def modpow(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Modular exponentiation. If exponent is -1, compute modular inverse."""
    modulus = engine.pop().get_integer()
    exponent = engine.pop().get_integer()
    value = engine.pop().get_integer()
    if exponent == -1:
        # Modular inverse
        result = pow(value, -1, modulus)
    else:
        result = pow(value, exponent, modulus)
    engine.push(Integer(result))


def shl(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Left shift integer."""
    shift = int(engine.pop().get_integer())
    engine.limits.assert_shift(shift)
    if shift == 0:
        return
    x = engine.pop().get_integer()
    engine.push(Integer(x << shift))


def shr(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Right shift integer."""
    shift = int(engine.pop().get_integer())
    engine.limits.assert_shift(shift)
    if shift == 0:
        return
    x = engine.pop().get_integer()
    engine.push(Integer(x >> shift))


def not_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Boolean NOT."""
    x = engine.pop().get_boolean()
    engine.push(Boolean(not x))


def booland(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Boolean AND."""
    x2 = engine.pop().get_boolean()
    x1 = engine.pop().get_boolean()
    engine.push(Boolean(x1 and x2))


def boolor(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Boolean OR."""
    x2 = engine.pop().get_boolean()
    x1 = engine.pop().get_boolean()
    engine.push(Boolean(x1 or x2))


def nz(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if integer is not zero."""
    x = engine.pop().get_integer()
    engine.push(Boolean(x != 0))


def numequal(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if two integers are equal."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Boolean(x1 == x2))


def numnotequal(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if two integers are not equal."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Boolean(x1 != x2))


def lt(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if x1 < x2."""
    x2 = engine.pop()
    x1 = engine.pop()
    if x1.is_null or x2.is_null:
        engine.push(Boolean(False))
    else:
        engine.push(Boolean(x1.get_integer() < x2.get_integer()))


def le(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if x1 <= x2."""
    x2 = engine.pop()
    x1 = engine.pop()
    if x1.is_null or x2.is_null:
        engine.push(Boolean(False))
    else:
        engine.push(Boolean(x1.get_integer() <= x2.get_integer()))


def gt(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if x1 > x2."""
    x2 = engine.pop()
    x1 = engine.pop()
    if x1.is_null or x2.is_null:
        engine.push(Boolean(False))
    else:
        engine.push(Boolean(x1.get_integer() > x2.get_integer()))


def ge(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if x1 >= x2."""
    x2 = engine.pop()
    x1 = engine.pop()
    if x1.is_null or x2.is_null:
        engine.push(Boolean(False))
    else:
        engine.push(Boolean(x1.get_integer() >= x2.get_integer()))


def min_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push minimum of two integers."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(min(x1, x2)))


def max_(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push maximum of two integers."""
    x2 = engine.pop().get_integer()
    x1 = engine.pop().get_integer()
    engine.push(Integer(max(x1, x2)))


def within(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Push true if x is within range [a, b)."""
    b = engine.pop().get_integer()
    a = engine.pop().get_integer()
    x = engine.pop().get_integer()
    engine.push(Boolean(a <= x < b))
