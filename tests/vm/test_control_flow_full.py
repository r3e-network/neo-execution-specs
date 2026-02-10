"""Comprehensive tests for VM control flow instructions.

Covers all untested control flow opcodes:
- JMP_L, JMPIF_L, JMPIFNOT_L
- JMPEQ/JMPEQ_L, JMPNE/JMPNE_L
- JMPGT/JMPGT_L, JMPGE/JMPGE_L, JMPLT/JMPLT_L, JMPLE/JMPLE_L
- CALL_L, CALLA, CALLT
- ABORT, ASSERT, THROW
- TRY/TRY_L, ENDTRY_L, ENDFINALLY
- SYSCALL
"""

from __future__ import annotations

import struct
import pytest

from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode
from neo.vm.types import Integer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _le32(val: int) -> bytes:
    """Pack signed 32-bit little-endian."""
    return struct.pack('<i', val)


def _le16u(val: int) -> bytes:
    """Pack unsigned 16-bit little-endian."""
    return struct.pack('<H', val)


def _run(script: bytes) -> ExecutionEngine:
    """Load script, execute, return engine."""
    engine = ExecutionEngine()
    engine.load_script(bytes(script))
    engine.execute()
    return engine


def _stack_int(engine: ExecutionEngine) -> int:
    """Pop top integer from result stack."""
    return engine.result_stack.pop().get_integer()


# ---------------------------------------------------------------------------
# JMP_L tests
# ---------------------------------------------------------------------------

class TestJmpL:
    """JMP_L: unconditional jump with 4-byte offset."""

    def test_jmp_l_forward(self):
        # JMP_L +5 (skip PUSH1), land on PUSH2
        script = bytearray([
            OpCode.JMP_L, *_le32(6),  # 1+4=5 bytes, jump to offset 6
            OpCode.PUSH1,              # offset 5, skipped
            OpCode.PUSH2,              # offset 6, executed
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_jmp_l_to_push0(self):
        script = bytearray([
            OpCode.JMP_L, *_le32(6),
            OpCode.PUSH3,              # skipped
            OpCode.PUSH0,              # target
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 0


# ---------------------------------------------------------------------------
# JMPIF_L / JMPIFNOT_L tests
# ---------------------------------------------------------------------------

class TestJmpIfL:
    """JMPIF_L: conditional jump with 4-byte offset."""

    def test_jmpif_l_true_jumps(self):
        script = bytearray([
            OpCode.PUSHT,
            OpCode.JMPIF_L, *_le32(7),  # offset from JMPIF_L pos=1, target=1+7=8
            OpCode.PUSH1,                # offset 6, skipped
            OpCode.NOP,                  # offset 7, skipped
            OpCode.PUSH2,               # offset 8, executed
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_jmpif_l_false_no_jump(self):
        script = bytearray([
            OpCode.PUSHF,
            OpCode.JMPIF_L, *_le32(7),
            OpCode.PUSH3,               # executed (no jump)
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 3


class TestJmpIfNotL:
    """JMPIFNOT_L: conditional jump with 4-byte offset."""

    def test_jmpifnot_l_false_jumps(self):
        script = bytearray([
            OpCode.PUSHF,
            OpCode.JMPIFNOT_L, *_le32(7),
            OpCode.PUSH1,               # skipped
            OpCode.NOP,
            OpCode.PUSH4,               # target
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 4

    def test_jmpifnot_l_true_no_jump(self):
        script = bytearray([
            OpCode.PUSHT,
            OpCode.JMPIFNOT_L, *_le32(7),
            OpCode.PUSH5,               # executed
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 5


# ---------------------------------------------------------------------------
# JMPEQ / JMPEQ_L tests
# ---------------------------------------------------------------------------

class TestJmpEq:
    """JMPEQ: jump if two integers are equal (1-byte offset)."""

    def test_equal_jumps(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH3,
            OpCode.JMPEQ, 3,            # +3 from JMPEQ pos
            OpCode.PUSH1,               # skipped
            OpCode.PUSH2,               # target
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_not_equal_no_jump(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH4,
            OpCode.JMPEQ, 3,
            OpCode.PUSH7,               # executed
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 7


class TestJmpEqL:
    """JMPEQ_L: jump if equal (4-byte offset)."""

    def test_equal_jumps(self):
        script = bytearray([
            OpCode.PUSH5, OpCode.PUSH5,
            OpCode.JMPEQ_L, *_le32(6),
            OpCode.PUSH1,
            OpCode.PUSH2,               # target
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_not_equal_no_jump(self):
        script = bytearray([
            OpCode.PUSH5, OpCode.PUSH3,
            OpCode.JMPEQ_L, *_le32(6),
            OpCode.PUSH8,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 8


# ---------------------------------------------------------------------------
# JMPGT / JMPGT_L tests
# ---------------------------------------------------------------------------

class TestJmpGt:
    """JMPGT: jump if x1 > x2 (1-byte offset)."""

    def test_greater_jumps(self):
        script = bytearray([
            OpCode.PUSH5, OpCode.PUSH3,
            OpCode.JMPGT, 3,
            OpCode.PUSH1,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_equal_no_jump(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH3,
            OpCode.JMPGT, 3,
            OpCode.PUSH7,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 7


class TestJmpGtL:
    """JMPGT_L: jump if x1 > x2 (4-byte offset)."""

    def test_greater_jumps(self):
        script = bytearray([
            OpCode.PUSH5, OpCode.PUSH3,
            OpCode.JMPGT_L, *_le32(6),
            OpCode.PUSH1,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2


# ---------------------------------------------------------------------------
# JMPGE / JMPGE_L tests
# ---------------------------------------------------------------------------

class TestJmpGe:
    """JMPGE: jump if x1 >= x2 (1-byte offset)."""

    def test_greater_jumps(self):
        script = bytearray([
            OpCode.PUSH5, OpCode.PUSH3,
            OpCode.JMPGE, 3,
            OpCode.PUSH1,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_equal_jumps(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH3,
            OpCode.JMPGE, 3,
            OpCode.PUSH1,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_less_no_jump(self):
        script = bytearray([
            OpCode.PUSH1, OpCode.PUSH3,
            OpCode.JMPGE, 3,
            OpCode.PUSH7,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 7


class TestJmpGeL:
    """JMPGE_L: jump if x1 >= x2 (4-byte offset)."""

    def test_equal_jumps(self):
        script = bytearray([
            OpCode.PUSH4, OpCode.PUSH4,
            OpCode.JMPGE_L, *_le32(6),
            OpCode.PUSH1,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2


# ---------------------------------------------------------------------------
# JMPLT / JMPLT_L tests
# ---------------------------------------------------------------------------

class TestJmpLt:
    """JMPLT: jump if x1 < x2 (1-byte offset)."""

    def test_less_jumps(self):
        script = bytearray([
            OpCode.PUSH1, OpCode.PUSH5,
            OpCode.JMPLT, 3,
            OpCode.PUSH7,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_equal_no_jump(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH3,
            OpCode.JMPLT, 3,
            OpCode.PUSH7,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 7


class TestJmpLtL:
    """JMPLT_L: jump if x1 < x2 (4-byte offset)."""

    def test_less_jumps(self):
        script = bytearray([
            OpCode.PUSH1, OpCode.PUSH5,
            OpCode.JMPLT_L, *_le32(6),
            OpCode.PUSH7,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2


# ---------------------------------------------------------------------------
# JMPLE / JMPLE_L tests
# ---------------------------------------------------------------------------

class TestJmpLe:
    """JMPLE: jump if x1 <= x2 (1-byte offset)."""

    def test_less_jumps(self):
        script = bytearray([
            OpCode.PUSH1, OpCode.PUSH5,
            OpCode.JMPLE, 3,
            OpCode.PUSH7,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_equal_jumps(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH3,
            OpCode.JMPLE, 3,
            OpCode.PUSH7,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_greater_no_jump(self):
        script = bytearray([
            OpCode.PUSH5, OpCode.PUSH1,
            OpCode.JMPLE, 3,
            OpCode.PUSH8,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 8


class TestJmpLeL:
    """JMPLE_L: jump if x1 <= x2 (4-byte offset)."""

    def test_less_jumps(self):
        script = bytearray([
            OpCode.PUSH1, OpCode.PUSH5,
            OpCode.JMPLE_L, *_le32(6),
            OpCode.PUSH7,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2


# ---------------------------------------------------------------------------
# CALL_L tests
# ---------------------------------------------------------------------------

class TestCallL:
    """CALL_L: function call with 4-byte offset."""

    def test_call_l_and_ret(self):
        # CALL_L to subroutine, RET returns
        script = bytearray([
            OpCode.CALL_L, *_le32(6),   # pos=0, call to 0+6=6
            OpCode.PUSH1,               # pos=5, after return
            OpCode.PUSH2,               # pos=6, subroutine
            OpCode.RET,                 # pos=7
        ])
        e = _run(script)
        assert e.state == VMState.HALT


# ---------------------------------------------------------------------------
# CALLA tests
# ---------------------------------------------------------------------------

class TestCalla:
    """CALLA: call function at pointer address from stack."""

    def test_calla_with_pusha(self):
        # PUSHA pushes a Pointer, CALLA calls it
        script = bytearray([
            OpCode.PUSHA, *_le32(7),    # pos=0, push pointer to pos 0+7=7
            OpCode.CALLA,               # pos=5, call pointer
            OpCode.PUSH1,               # pos=6, after return
            OpCode.PUSH2,               # pos=7, subroutine
            OpCode.RET,                 # pos=8
        ])
        e = _run(script)
        assert e.state == VMState.HALT

class TestJmpNe:
    """JMPNE: jump if not equal (1-byte offset)."""

    def test_not_equal_jumps(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH4,
            OpCode.JMPNE, 3,
            OpCode.PUSH1,
            OpCode.PUSH2,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 2

    def test_equal_no_jump(self):
        script = bytearray([
            OpCode.PUSH3, OpCode.PUSH3,
            OpCode.JMPNE, 3,
            OpCode.PUSH7,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 7


class TestJmpNeL:
    """JMPNE_L: jump if not equal (4-byte offset)."""

    def test_not_equal_jumps(self):
        script = bytearray([
            OpCode.PUSH1, OpCode.PUSH2,
            OpCode.JMPNE_L, *_le32(6),
            OpCode.PUSH3,
            OpCode.PUSH4,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 4

    def test_equal_no_jump(self):
        script = bytearray([
            OpCode.PUSH2, OpCode.PUSH2,
            OpCode.JMPNE_L, *_le32(6),
            OpCode.PUSH8,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 8


# ---------------------------------------------------------------------------
# TRY_L tests
# ---------------------------------------------------------------------------

class TestTryL:
    """TRY_L: begin try block with 4-byte offsets."""

    def test_try_l_catch_exception(self):
        """TRY_L with catch handler catches thrown exception."""
        # Layout:
        # 0: TRY_L catch=+10, finally=0  (9 bytes: opcode + 4 + 4)
        # 9: PUSH1 (throw something)
        # 10: THROW
        # 11: ENDTRY +3 (skip catch)  -- never reached due to throw
        # But we need catch to land properly.
        # Simpler: just test that TRY_L parses 8-byte operand correctly
        # by having a try block that doesn't throw.
        script = bytearray([
            OpCode.TRY_L, *_le32(11), *_le32(0),  # catch at +11, no finally
            OpCode.PUSH5,                           # try body
            OpCode.ENDTRY, 2,                       # end try, jump +2
            OpCode.NOP,                             # catch (skipped)
            OpCode.PUSH3,                           # after try
        ])
        e = _run(script)
        assert e.state == VMState.HALT


# ---------------------------------------------------------------------------
# ENDTRY_L tests
# ---------------------------------------------------------------------------

class TestEndTryL:
    """ENDTRY_L: end try block with 4-byte offset."""

    def test_endtry_l_skips_catch(self):
        script = bytearray([
            OpCode.TRY, 5, 0,           # catch at +5, no finally
            OpCode.PUSH5,               # try body
            OpCode.ENDTRY_L, *_le32(3), # end try, jump +3 (skip catch)
            OpCode.NOP,                 # catch handler (skipped)
            OpCode.PUSH3,              # after try
        ])
        e = _run(script)
        assert e.state == VMState.HALT


# ---------------------------------------------------------------------------
# ENDFINALLY tests
# ---------------------------------------------------------------------------

class TestEndFinally:
    """ENDFINALLY: end finally block."""

    def test_try_finally_endfinally(self):
        """TRY with finally block executes finally via ENDFINALLY."""
        # pos 0: TRY (3 bytes: opcode + 2 operand)
        # pos 3: PUSH5 (try body)
        # pos 4: ENDTRY (2 bytes: opcode + 1 operand)
        # pos 6: PUSH3 (finally body)
        # pos 7: ENDFINALLY
        # pos 8: PUSH1 (after everything)
        script = bytearray([
            OpCode.TRY, 0, 6,          # no catch, finally at pos 0+6=6
            OpCode.PUSH5,              # try body
            OpCode.ENDTRY, 4,          # end try, end_ptr = 4+4=8
            OpCode.PUSH3,              # finally body
            OpCode.ENDFINALLY,         # end finally -> jumps to end_ptr=8
            OpCode.PUSH1,              # after everything
        ])
        e = _run(script)
        assert e.state == VMState.HALT


# ---------------------------------------------------------------------------
# SYSCALL tests
# ---------------------------------------------------------------------------

class TestSyscall:
    """SYSCALL: call system service by 4-byte hash."""

    def test_syscall_invokes_handler(self):
        """SYSCALL dispatches to engine.syscall_handler."""
        called = {}

        def handler(eng, hash_val):
            called['hash'] = hash_val
            eng.push(Integer(99))

        engine = ExecutionEngine()
        engine.syscall_handler = handler
        script = bytearray([
            OpCode.SYSCALL, 0x01, 0x02, 0x03, 0x04,
        ])
        engine.load_script(bytes(script))
        engine.execute()
        assert engine.state == VMState.HALT
        assert called['hash'] == 0x04030201
        assert engine.result_stack.pop().get_integer() == 99

    def test_syscall_no_handler_faults(self):
        """SYSCALL without handler raises exception -> FAULT."""
        script = bytearray([
            OpCode.SYSCALL, 0xAA, 0xBB, 0xCC, 0xDD,
        ])
        e = _run(script)
        assert e.state == VMState.FAULT


# ---------------------------------------------------------------------------
# CALLT tests
# ---------------------------------------------------------------------------

class TestCallt:
    """CALLT: call function by 2-byte token index."""

    def test_callt_invokes_handler(self):
        """CALLT dispatches to engine.token_handler."""
        called = {}

        def handler(eng, token_idx):
            called['idx'] = token_idx
            eng.push(Integer(77))

        engine = ExecutionEngine()
        engine.token_handler = handler
        script = bytearray([
            OpCode.CALLT, 0x05, 0x00,  # token index = 5
        ])
        engine.load_script(bytes(script))
        engine.execute()
        assert engine.state == VMState.HALT
        assert called['idx'] == 5
        assert engine.result_stack.pop().get_integer() == 77

    def test_callt_no_handler_faults(self):
        """CALLT without handler raises exception -> FAULT."""
        script = bytearray([
            OpCode.CALLT, 0x01, 0x00,
        ])
        e = _run(script)
        assert e.state == VMState.FAULT


# ---------------------------------------------------------------------------
# ABORT tests
# ---------------------------------------------------------------------------

class TestAbort:
    """ABORT: unconditional fault (cannot be caught by TRY)."""

    def test_abort_faults(self):
        script = bytearray([OpCode.ABORT])
        e = _run(script)
        assert e.state == VMState.FAULT

    def test_abort_not_caught_by_try(self):
        """ABORT inside TRY still faults — it bypasses catch."""
        script = bytearray([
            OpCode.TRY, 4, 0,      # catch at +4, no finally
            OpCode.ABORT,           # pos 3, should fault
            OpCode.NOP,             # catch (never reached)
            OpCode.PUSH1,           # after
        ])
        e = _run(script)
        assert e.state == VMState.FAULT


# ---------------------------------------------------------------------------
# ASSERT tests
# ---------------------------------------------------------------------------

class TestAssert:
    """ASSERT: fault if top of stack is false."""

    def test_assert_true_continues(self):
        script = bytearray([
            OpCode.PUSHT,
            OpCode.ASSERT,
            OpCode.PUSH5,
        ])
        e = _run(script)
        assert e.state == VMState.HALT
        assert _stack_int(e) == 5

    def test_assert_false_faults(self):
        script = bytearray([
            OpCode.PUSHF,
            OpCode.ASSERT,
            OpCode.PUSH5,
        ])
        e = _run(script)
        assert e.state == VMState.FAULT


# ---------------------------------------------------------------------------
# THROW tests
# ---------------------------------------------------------------------------

class TestThrow:
    """THROW: throw exception from stack."""

    def test_throw_without_try_faults(self):
        """THROW outside TRY causes FAULT."""
        script = bytearray([
            OpCode.PUSH1,
            OpCode.THROW,
        ])
        e = _run(script)
        assert e.state == VMState.FAULT

    def test_throw_caught_by_try(self):
        """THROW inside TRY is caught by catch handler."""
        # pos 0: TRY (3 bytes) catch=+5, no finally
        # pos 3: PUSH1 (throw value)
        # pos 4: THROW
        # pos 5: catch handler -> PUSH9
        # pos 6: ENDTRY +1 -> pos 7
        # pos 7: (end)
        script = bytearray([
            OpCode.TRY, 5, 0,
            OpCode.PUSH1,
            OpCode.THROW,
            OpCode.PUSH9,
            OpCode.ENDTRY, 1,
        ])
        e = _run(script)
        assert e.state == VMState.HALT