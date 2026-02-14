"""NeoVM Execution Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Dict, List, Optional

from neo.exceptions import InvalidOperationException, StackOverflowException, VMAbortException
from neo.vm.evaluation_stack import EvaluationStack
from neo.vm.exception_handling import (
    ExceptionHandlingContext,
    ExceptionHandlingState,
    TryStack,
)
from neo.vm.execution_context import ExecutionContext, Instruction
from neo.vm.gas import get_price
from neo.vm.limits import ExecutionEngineLimits
from neo.vm.opcode import OpCode
from neo.vm.reference_counter import ReferenceCounter
from neo.vm.slot import Slot
from neo.vm.types import StackItem


class VMState(IntEnum):
    NONE = 0
    HALT = 1
    FAULT = 2
    BREAK = 4


class VMUnhandledException(Exception):
    def __init__(self, exception: StackItem):
        self.exception = exception
        super().__init__(f"Unhandled VM exception: {exception}")


@dataclass
class ExecutionEngine:
    limits: ExecutionEngineLimits = field(default_factory=ExecutionEngineLimits)
    invocation_stack: List[ExecutionContext] = field(default_factory=list)
    result_stack: EvaluationStack = field(default_factory=EvaluationStack)
    state: VMState = VMState.NONE
    uncaught_exception: Optional[StackItem] = None
    is_jumping: bool = False
    reference_counter: Optional[ReferenceCounter] = None
    gas_consumed: int = 0
    gas_limit: int = -1  # -1 means unlimited (pure VM mode)
    syscall_handler: Optional[Callable[[ExecutionEngine, int], None]] = None
    token_handler: Optional[Callable[[ExecutionEngine, int], None]] = None
    _handlers: Dict[int, Callable] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if self.reference_counter is None:
            self.reference_counter = ReferenceCounter()
        self._init_handlers()

    @property
    def current_context(self) -> ExecutionContext:
        if not self.invocation_stack:
            raise InvalidOperationException("No current execution context")
        return self.invocation_stack[-1]

    def load_script(self, script: bytes, rv_count: int = -1) -> ExecutionContext:
        ctx = ExecutionContext(
            script=script, rv_count=rv_count, reference_counter=self.reference_counter
        )
        self.load_context(ctx)
        return ctx

    def load_context(self, context: ExecutionContext) -> None:
        if len(self.invocation_stack) >= self.limits.max_invocation_stack_size:
            raise StackOverflowException("Invocation stack overflow")
        self.invocation_stack.append(context)

    def execute(self) -> VMState:
        self.state = VMState.NONE
        while self.state == VMState.NONE:
            self.execute_next()
        return self.state

    def execute_next(self) -> None:
        if not self.invocation_stack:
            self.state = VMState.HALT
            return
        ctx = self.invocation_stack[-1]
        instr = ctx.current_instruction
        if instr is None:
            ctx_pop = self.invocation_stack.pop()
            if ctx_pop.rv_count >= 0 and len(ctx_pop.evaluation_stack) != ctx_pop.rv_count:
                raise InvalidOperationException(
                    f"Return value count mismatch: expected {ctx_pop.rv_count}, "
                    f"got {len(ctx_pop.evaluation_stack)}"
                )
            target = (
                self.invocation_stack[-1].evaluation_stack
                if self.invocation_stack
                else self.result_stack
            )
            if ctx_pop.evaluation_stack is not target:
                ctx_pop.evaluation_stack.copy_to(target)
            if not self.invocation_stack:
                self.state = VMState.HALT
            return
        try:
            self.is_jumping = False
            self.add_gas(get_price(instr.opcode))
            handler = self._handlers.get(instr.opcode)
            if handler is None:
                raise InvalidOperationException(f"Unknown opcode: {instr.opcode:#04x}")
            handler(self, instr)
            if not self.is_jumping:
                ctx.move_next()
        except VMUnhandledException as e:
            self.uncaught_exception = e.exception
            self.state = VMState.FAULT
        except VMAbortException:
            # ABORT is uncatchable — bypass VM try/catch, fault immediately.
            self.state = VMState.FAULT
        except Exception as e:
            from neo.exceptions import OutOfGasException

            if isinstance(e, OutOfGasException):
                raise
            # Route through VM try/catch before faulting.
            # C# reference: ExecutionEngine.ExecuteInstruction catches
            # exceptions and calls HandleException, which searches the
            # try-stack for a matching catch/finally handler.
            from neo.vm.types import ByteString

            ex_item = ByteString(str(e).encode("utf-8"))
            try:
                self.execute_throw(ex_item)
            except VMUnhandledException:
                self.uncaught_exception = ex_item
                self.state = VMState.FAULT

    def add_gas(self, gas: int) -> None:
        """Add gas consumed and check against limit.

        Raises OutOfGasException if gas_limit is exceeded.
        gas_limit == -1 means unlimited (pure VM mode).
        """
        self.gas_consumed += gas
        if self.gas_limit >= 0 and self.gas_consumed > self.gas_limit:
            from neo.exceptions import OutOfGasException

            raise OutOfGasException("Insufficient GAS")

    def push(self, item: StackItem) -> None:
        self.current_context.evaluation_stack.push(item)

    def pop(self) -> StackItem:
        return self.current_context.evaluation_stack.pop()

    def peek(self, index: int = 0) -> StackItem:
        return self.current_context.evaluation_stack.peek(index)

    def create_slot(self, count: int) -> Slot:
        return Slot(count, self.reference_counter)

    def create_slot_from_items(self, items: List[StackItem]) -> Slot:
        return Slot.from_items(items, self.reference_counter)

    def execute_jump(self, position: int) -> None:
        if position < 0 or position >= len(self.current_context.script):
            raise InvalidOperationException(f"Jump target {position} out of range")
        self.current_context.ip = position
        self.is_jumping = True

    def execute_jump_offset(self, offset: int) -> None:
        self.execute_jump(self.current_context.ip + offset)

    def execute_call(self, position: int) -> None:
        self.load_context(self.current_context.clone(position))

    def execute_ret(self) -> None:
        ctx_pop = self.invocation_stack.pop()
        target = (
            self.invocation_stack[-1].evaluation_stack
            if self.invocation_stack
            else self.result_stack
        )
        if ctx_pop.evaluation_stack is not target:
            if ctx_pop.rv_count >= 0 and len(ctx_pop.evaluation_stack) != ctx_pop.rv_count:
                raise InvalidOperationException("Return value count mismatch")
            ctx_pop.evaluation_stack.copy_to(target)
        if not self.invocation_stack:
            self.state = VMState.HALT
        self.is_jumping = True

    def execute_try(self, catch_offset: int, finally_offset: int) -> None:
        if catch_offset == 0 and finally_offset == 0:
            raise InvalidOperationException("Both offsets can't be 0")
        ctx = self.current_context
        if ctx.try_stack is None:
            ctx.try_stack = TryStack()
        elif len(ctx.try_stack) >= self.limits.max_try_nesting_depth:
            raise InvalidOperationException("MaxTryNestingDepth exceeded")
        catch_ptr = -1 if catch_offset == 0 else ctx.ip + catch_offset
        finally_ptr = -1 if finally_offset == 0 else ctx.ip + finally_offset
        ctx.try_stack.push(ExceptionHandlingContext(catch_ptr, finally_ptr))

    def execute_endtry(self, end_offset: int) -> None:
        ctx = self.current_context
        if ctx.try_stack is None or len(ctx.try_stack) == 0:
            raise InvalidOperationException("No TRY block")
        current_try = ctx.try_stack.peek()
        if current_try.state == ExceptionHandlingState.FINALLY:
            raise InvalidOperationException("ENDTRY in FINALLY")
        end_ptr = ctx.ip + end_offset
        if current_try.has_finally:
            current_try.state = ExceptionHandlingState.FINALLY
            current_try.end_pointer = end_ptr
            ctx.ip = current_try.finally_pointer
        else:
            ctx.try_stack.pop()
            ctx.ip = end_ptr
        self.is_jumping = True

    def execute_endfinally(self) -> None:
        ctx = self.current_context
        if ctx.try_stack is None or len(ctx.try_stack) == 0:
            raise InvalidOperationException("No TRY block")
        current_try = ctx.try_stack.pop()
        if self.uncaught_exception is None:
            ctx.ip = current_try.end_pointer
        else:
            self.execute_throw(self.uncaught_exception)
        self.is_jumping = True

    def execute_throw(self, ex: StackItem) -> None:
        self.uncaught_exception = ex
        pop_count = 0
        # Iterate from top of invocation stack (last element = top)
        for i in range(len(self.invocation_stack) - 1, -1, -1):
            context = self.invocation_stack[i]
            if context.try_stack is not None:
                while len(context.try_stack) > 0:
                    try_ctx = context.try_stack.peek()
                    if try_ctx.state == ExceptionHandlingState.FINALLY:
                        context.try_stack.pop()
                        continue
                    if try_ctx.state == ExceptionHandlingState.CATCH and not try_ctx.has_finally:
                        context.try_stack.pop()
                        continue
                    # Pop contexts above the handler (safe: we iterate by index)
                    while len(self.invocation_stack) > i + 1:
                        self.invocation_stack.pop()
                    if try_ctx.state == ExceptionHandlingState.TRY and try_ctx.has_catch:
                        try_ctx.state = ExceptionHandlingState.CATCH
                        self.push(self.uncaught_exception)
                        context.ip = try_ctx.catch_pointer
                        self.uncaught_exception = None
                    else:
                        try_ctx.state = ExceptionHandlingState.FINALLY
                        context.ip = try_ctx.finally_pointer
                    self.is_jumping = True
                    return
            pop_count += 1
        raise VMUnhandledException(self.uncaught_exception)

    def _init_handlers(self) -> None:
        from neo.vm.instructions import (
            bitwise,
            compound,
            constants,
            control_flow,
            numeric,
            slot,
            splice,
            stack,
            types,
        )

        # Constants
        self._handlers[OpCode.PUSHINT8] = constants.pushint8
        self._handlers[OpCode.PUSHINT16] = constants.pushint16
        self._handlers[OpCode.PUSHINT32] = constants.pushint32
        self._handlers[OpCode.PUSHINT64] = constants.pushint64
        self._handlers[OpCode.PUSHINT128] = constants.pushint128
        self._handlers[OpCode.PUSHINT256] = constants.pushint256
        self._handlers[OpCode.PUSHT] = constants.pusht
        self._handlers[OpCode.PUSHF] = constants.pushf
        self._handlers[OpCode.PUSHA] = constants.pusha
        self._handlers[OpCode.PUSHNULL] = constants.pushnull
        self._handlers[OpCode.PUSHDATA1] = constants.pushdata1
        self._handlers[OpCode.PUSHDATA2] = constants.pushdata2
        self._handlers[OpCode.PUSHDATA4] = constants.pushdata4
        self._handlers[OpCode.PUSHM1] = constants.pushm1
        for i in range(17):
            self._handlers[OpCode.PUSH0 + i] = getattr(constants, f"push{i}")

        # Control flow
        self._handlers[OpCode.NOP] = control_flow.nop
        self._handlers[OpCode.JMP] = control_flow.jmp
        self._handlers[OpCode.JMP_L] = control_flow.jmp_l
        self._handlers[OpCode.JMPIF] = control_flow.jmpif
        self._handlers[OpCode.JMPIF_L] = control_flow.jmpif_l
        self._handlers[OpCode.JMPIFNOT] = control_flow.jmpifnot
        self._handlers[OpCode.JMPIFNOT_L] = control_flow.jmpifnot_l
        self._handlers[OpCode.JMPEQ] = control_flow.jmpeq
        self._handlers[OpCode.JMPEQ_L] = control_flow.jmpeq_l
        self._handlers[OpCode.JMPNE] = control_flow.jmpne
        self._handlers[OpCode.JMPNE_L] = control_flow.jmpne_l
        self._handlers[OpCode.JMPGT] = control_flow.jmpgt
        self._handlers[OpCode.JMPGT_L] = control_flow.jmpgt_l
        self._handlers[OpCode.JMPGE] = control_flow.jmpge
        self._handlers[OpCode.JMPGE_L] = control_flow.jmpge_l
        self._handlers[OpCode.JMPLT] = control_flow.jmplt
        self._handlers[OpCode.JMPLT_L] = control_flow.jmplt_l
        self._handlers[OpCode.JMPLE] = control_flow.jmple
        self._handlers[OpCode.JMPLE_L] = control_flow.jmple_l
        self._handlers[OpCode.CALL] = control_flow.call
        self._handlers[OpCode.CALL_L] = control_flow.call_l
        self._handlers[OpCode.CALLA] = control_flow.calla
        self._handlers[OpCode.CALLT] = control_flow.callt
        self._handlers[OpCode.ABORT] = control_flow.abort
        self._handlers[OpCode.ASSERT] = control_flow.assert_
        self._handlers[OpCode.THROW] = control_flow.throw
        self._handlers[OpCode.TRY] = control_flow.try_
        self._handlers[OpCode.TRY_L] = control_flow.try_l
        self._handlers[OpCode.ENDTRY] = control_flow.endtry
        self._handlers[OpCode.ENDTRY_L] = control_flow.endtry_l
        self._handlers[OpCode.ENDFINALLY] = control_flow.endfinally
        self._handlers[OpCode.RET] = control_flow.ret
        self._handlers[OpCode.SYSCALL] = control_flow.syscall

        # Stack
        self._handlers[OpCode.DEPTH] = stack.depth
        self._handlers[OpCode.DROP] = stack.drop
        self._handlers[OpCode.NIP] = stack.nip
        self._handlers[OpCode.XDROP] = stack.xdrop
        self._handlers[OpCode.CLEAR] = stack.clear
        self._handlers[OpCode.DUP] = stack.dup
        self._handlers[OpCode.OVER] = stack.over
        self._handlers[OpCode.PICK] = stack.pick
        self._handlers[OpCode.TUCK] = stack.tuck
        self._handlers[OpCode.SWAP] = stack.swap
        self._handlers[OpCode.ROT] = stack.rot
        self._handlers[OpCode.ROLL] = stack.roll
        self._handlers[OpCode.REVERSE3] = stack.reverse3
        self._handlers[OpCode.REVERSE4] = stack.reverse4
        self._handlers[OpCode.REVERSEN] = stack.reversen

        # Slot
        self._handlers[OpCode.INITSSLOT] = slot.initsslot
        self._handlers[OpCode.INITSLOT] = slot.initslot
        for i in range(7):
            self._handlers[OpCode.LDSFLD0 + i] = getattr(slot, f"ldsfld{i}")
            self._handlers[OpCode.STSFLD0 + i] = getattr(slot, f"stsfld{i}")
            self._handlers[OpCode.LDLOC0 + i] = getattr(slot, f"ldloc{i}")
            self._handlers[OpCode.STLOC0 + i] = getattr(slot, f"stloc{i}")
            self._handlers[OpCode.LDARG0 + i] = getattr(slot, f"ldarg{i}")
            self._handlers[OpCode.STARG0 + i] = getattr(slot, f"starg{i}")
        self._handlers[OpCode.LDSFLD] = slot.ldsfld
        self._handlers[OpCode.STSFLD] = slot.stsfld
        self._handlers[OpCode.LDLOC] = slot.ldloc
        self._handlers[OpCode.STLOC] = slot.stloc
        self._handlers[OpCode.LDARG] = slot.ldarg
        self._handlers[OpCode.STARG] = slot.starg

        # Splice
        self._handlers[OpCode.NEWBUFFER] = splice.newbuffer
        self._handlers[OpCode.MEMCPY] = splice.memcpy
        self._handlers[OpCode.CAT] = splice.cat
        self._handlers[OpCode.SUBSTR] = splice.substr
        self._handlers[OpCode.LEFT] = splice.left
        self._handlers[OpCode.RIGHT] = splice.right

        # Bitwise
        self._handlers[OpCode.INVERT] = bitwise.invert
        self._handlers[OpCode.AND] = bitwise.and_
        self._handlers[OpCode.OR] = bitwise.or_
        self._handlers[OpCode.XOR] = bitwise.xor
        self._handlers[OpCode.EQUAL] = bitwise.equal
        self._handlers[OpCode.NOTEQUAL] = bitwise.notequal

        # Numeric
        self._handlers[OpCode.SIGN] = numeric.sign
        self._handlers[OpCode.ABS] = numeric.abs_
        self._handlers[OpCode.NEGATE] = numeric.negate
        self._handlers[OpCode.INC] = numeric.inc
        self._handlers[OpCode.DEC] = numeric.dec
        self._handlers[OpCode.ADD] = numeric.add
        self._handlers[OpCode.SUB] = numeric.sub
        self._handlers[OpCode.MUL] = numeric.mul
        self._handlers[OpCode.DIV] = numeric.div
        self._handlers[OpCode.MOD] = numeric.mod
        self._handlers[OpCode.POW] = numeric.pow_
        self._handlers[OpCode.SQRT] = numeric.sqrt
        self._handlers[OpCode.MODMUL] = numeric.modmul
        self._handlers[OpCode.MODPOW] = numeric.modpow
        self._handlers[OpCode.SHL] = numeric.shl
        self._handlers[OpCode.SHR] = numeric.shr
        self._handlers[OpCode.NOT] = numeric.not_
        self._handlers[OpCode.BOOLAND] = numeric.booland
        self._handlers[OpCode.BOOLOR] = numeric.boolor
        self._handlers[OpCode.NZ] = numeric.nz
        self._handlers[OpCode.NUMEQUAL] = numeric.numequal
        self._handlers[OpCode.NUMNOTEQUAL] = numeric.numnotequal
        self._handlers[OpCode.LT] = numeric.lt
        self._handlers[OpCode.LE] = numeric.le
        self._handlers[OpCode.GT] = numeric.gt
        self._handlers[OpCode.GE] = numeric.ge
        self._handlers[OpCode.MIN] = numeric.min_
        self._handlers[OpCode.MAX] = numeric.max_
        self._handlers[OpCode.WITHIN] = numeric.within

        # Compound types
        self._handlers[OpCode.PACKMAP] = compound.packmap
        self._handlers[OpCode.PACKSTRUCT] = compound.packstruct
        self._handlers[OpCode.PACK] = compound.pack
        self._handlers[OpCode.UNPACK] = compound.unpack
        self._handlers[OpCode.NEWARRAY0] = compound.newarray0
        self._handlers[OpCode.NEWARRAY] = compound.newarray
        self._handlers[OpCode.NEWARRAY_T] = compound.newarray_t
        self._handlers[OpCode.NEWSTRUCT0] = compound.newstruct0
        self._handlers[OpCode.NEWSTRUCT] = compound.newstruct
        self._handlers[OpCode.NEWMAP] = compound.newmap
        self._handlers[OpCode.SIZE] = compound.size
        self._handlers[OpCode.HASKEY] = compound.haskey
        self._handlers[OpCode.KEYS] = compound.keys
        self._handlers[OpCode.VALUES] = compound.values
        self._handlers[OpCode.PICKITEM] = compound.pickitem
        self._handlers[OpCode.APPEND] = compound.append
        self._handlers[OpCode.SETITEM] = compound.setitem
        self._handlers[OpCode.REVERSEITEMS] = compound.reverseitems
        self._handlers[OpCode.REMOVE] = compound.remove
        self._handlers[OpCode.CLEARITEMS] = compound.clearitems
        self._handlers[OpCode.POPITEM] = compound.popitem

        # Types
        self._handlers[OpCode.ISNULL] = types.isnull
        self._handlers[OpCode.ISTYPE] = types.istype
        self._handlers[OpCode.CONVERT] = types.convert
        self._handlers[OpCode.ABORTMSG] = types.abortmsg
        self._handlers[OpCode.ASSERTMSG] = types.assertmsg


__all__ = [
    "ExecutionEngine",
    "Instruction",
    "VMState",
    "VMUnhandledException",
]
