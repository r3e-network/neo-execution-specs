"""Comparison instructions for NeoVM.

This module provides standalone comparison functions that work with
ExecutionContext directly. These are used for testing and can also
be used for simpler comparison operations.

Functions:
    lt: Less than comparison
    le: Less than or equal comparison
    gt: Greater than comparison
    ge: Greater than or equal comparison
"""

from neo.vm.types import Boolean


def lt(ctx) -> None:
    """Push true if x1 < x2.

    Pops two integers from the stack and pushes True if the first
    is less than the second, False otherwise.
    """
    x2 = ctx.evaluation_stack.pop()
    x1 = ctx.evaluation_stack.pop()
    if x1.is_null or x2.is_null:
        ctx.evaluation_stack.push(Boolean(False))
    else:
        ctx.evaluation_stack.push(Boolean(x1.get_integer() < x2.get_integer()))


def le(ctx) -> None:
    """Push true if x1 <= x2.

    Pops two integers from the stack and pushes True if the first
    is less than or equal to the second, False otherwise.
    """
    x2 = ctx.evaluation_stack.pop()
    x1 = ctx.evaluation_stack.pop()
    if x1.is_null or x2.is_null:
        ctx.evaluation_stack.push(Boolean(False))
    else:
        ctx.evaluation_stack.push(Boolean(x1.get_integer() <= x2.get_integer()))


def gt(ctx) -> None:
    """Push true if x1 > x2.

    Pops two integers from the stack and pushes True if the first
    is greater than the second, False otherwise.
    """
    x2 = ctx.evaluation_stack.pop()
    x1 = ctx.evaluation_stack.pop()
    if x1.is_null or x2.is_null:
        ctx.evaluation_stack.push(Boolean(False))
    else:
        ctx.evaluation_stack.push(Boolean(x1.get_integer() > x2.get_integer()))


def ge(ctx) -> None:
    """Push true if x1 >= x2.

    Pops two integers from the stack and pushes True if the first
    is greater than or equal to the second, False otherwise.
    """
    x2 = ctx.evaluation_stack.pop()
    x1 = ctx.evaluation_stack.pop()
    if x1.is_null or x2.is_null:
        ctx.evaluation_stack.push(Boolean(False))
    else:
        ctx.evaluation_stack.push(Boolean(x1.get_integer() >= x2.get_integer()))
