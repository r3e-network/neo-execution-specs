"""Neo N3 GAS costs per opcode.

Based on the Neo N3 reference implementation (neo-vm OpCode prices).
Prices are in base fee units; the execution fee factor multiplies these.
"""

from neo.vm.opcode import OpCode

# Complete opcode price table from Neo N3 reference
OPCODE_PRICE = {
    # region Constants (0x00-0x20)
    OpCode.PUSHINT8: 1,
    OpCode.PUSHINT16: 1,
    OpCode.PUSHINT32: 1,
    OpCode.PUSHINT64: 1,
    OpCode.PUSHINT128: 4,
    OpCode.PUSHINT256: 4,
    OpCode.PUSHT: 1,
    OpCode.PUSHF: 1,
    OpCode.PUSHA: 4,
    OpCode.PUSHNULL: 1,
    OpCode.PUSHDATA1: 8,
    OpCode.PUSHDATA2: 512,
    OpCode.PUSHDATA4: 4096,
    OpCode.PUSHM1: 1,
    # PUSH0 through PUSH16
    OpCode.PUSH0: 1,
    OpCode.PUSH1: 1,
    OpCode.PUSH2: 1,
    OpCode.PUSH3: 1,
    OpCode.PUSH4: 1,
    OpCode.PUSH5: 1,
    OpCode.PUSH6: 1,
    OpCode.PUSH7: 1,
    OpCode.PUSH8: 1,
    OpCode.PUSH9: 1,
    OpCode.PUSH10: 1,
    OpCode.PUSH11: 1,
    OpCode.PUSH12: 1,
    OpCode.PUSH13: 1,
    OpCode.PUSH14: 1,
    OpCode.PUSH15: 1,
    OpCode.PUSH16: 1,
    # endregion

    # region Flow Control (0x21-0x41)
    OpCode.NOP: 1,
    OpCode.JMP: 2,
    OpCode.JMP_L: 2,
    OpCode.JMPIF: 2,
    OpCode.JMPIF_L: 2,
    OpCode.JMPIFNOT: 2,
    OpCode.JMPIFNOT_L: 2,
    OpCode.JMPEQ: 2,
    OpCode.JMPEQ_L: 2,
    OpCode.JMPNE: 2,
    OpCode.JMPNE_L: 2,
    OpCode.JMPGT: 2,
    OpCode.JMPGT_L: 2,
    OpCode.JMPGE: 2,
    OpCode.JMPGE_L: 2,
    OpCode.JMPLT: 2,
    OpCode.JMPLT_L: 2,
    OpCode.JMPLE: 2,
    OpCode.JMPLE_L: 2,
    OpCode.CALL: 512,
    OpCode.CALL_L: 512,
    OpCode.CALLA: 512,
    OpCode.CALLT: 32768,
    OpCode.ABORT: 0,
    OpCode.ASSERT: 1,
    OpCode.THROW: 512,
    OpCode.TRY: 4,
    OpCode.TRY_L: 4,
    OpCode.ENDTRY: 4,
    OpCode.ENDTRY_L: 4,
    OpCode.ENDFINALLY: 4,
    OpCode.RET: 0,
    OpCode.SYSCALL: 0,  # syscall cost charged separately
    # endregion

    # region Stack (0x43-0x55)
    OpCode.DEPTH: 2,
    OpCode.DROP: 2,
    OpCode.NIP: 2,
    OpCode.XDROP: 16,
    OpCode.CLEAR: 16,
    OpCode.DUP: 2,
    OpCode.OVER: 2,
    OpCode.PICK: 2,
    OpCode.TUCK: 2,
    OpCode.SWAP: 2,
    OpCode.ROT: 2,
    OpCode.ROLL: 16,
    OpCode.REVERSE3: 2,
    OpCode.REVERSE4: 2,
    OpCode.REVERSEN: 16,
    # endregion

    # region Slot (0x56-0x87)
    OpCode.INITSSLOT: 16,
    OpCode.INITSLOT: 64,
    OpCode.LDSFLD0: 2,
    OpCode.LDSFLD1: 2,
    OpCode.LDSFLD2: 2,
    OpCode.LDSFLD3: 2,
    OpCode.LDSFLD4: 2,
    OpCode.LDSFLD5: 2,
    OpCode.LDSFLD6: 2,
    OpCode.LDSFLD: 2,
    OpCode.STSFLD0: 2,
    OpCode.STSFLD1: 2,
    OpCode.STSFLD2: 2,
    OpCode.STSFLD3: 2,
    OpCode.STSFLD4: 2,
    OpCode.STSFLD5: 2,
    OpCode.STSFLD6: 2,
    OpCode.STSFLD: 2,
    OpCode.LDLOC0: 2,
    OpCode.LDLOC1: 2,
    OpCode.LDLOC2: 2,
    OpCode.LDLOC3: 2,
    OpCode.LDLOC4: 2,
    OpCode.LDLOC5: 2,
    OpCode.LDLOC6: 2,
    OpCode.LDLOC: 2,
    OpCode.STLOC0: 2,
    OpCode.STLOC1: 2,
    OpCode.STLOC2: 2,
    OpCode.STLOC3: 2,
    OpCode.STLOC4: 2,
    OpCode.STLOC5: 2,
    OpCode.STLOC6: 2,
    OpCode.STLOC: 2,
    OpCode.LDARG0: 2,
    OpCode.LDARG1: 2,
    OpCode.LDARG2: 2,
    OpCode.LDARG3: 2,
    OpCode.LDARG4: 2,
    OpCode.LDARG5: 2,
    OpCode.LDARG6: 2,
    OpCode.LDARG: 2,
    OpCode.STARG0: 2,
    OpCode.STARG1: 2,
    OpCode.STARG2: 2,
    OpCode.STARG3: 2,
    OpCode.STARG4: 2,
    OpCode.STARG5: 2,
    OpCode.STARG6: 2,
    OpCode.STARG: 2,
    # endregion

    # region Splice (0x88-0x8E)
    OpCode.NEWBUFFER: 256,
    OpCode.MEMCPY: 2048,
    OpCode.CAT: 2048,
    OpCode.SUBSTR: 2048,
    OpCode.LEFT: 2048,
    OpCode.RIGHT: 2048,
    # endregion

    # region Bitwise (0x90-0x98)
    OpCode.INVERT: 4,
    OpCode.AND: 8,
    OpCode.OR: 8,
    OpCode.XOR: 8,
    OpCode.EQUAL: 32,
    OpCode.NOTEQUAL: 32,
    # endregion

    # region Numeric (0x99-0xBB)
    OpCode.SIGN: 4,
    OpCode.ABS: 4,
    OpCode.NEGATE: 4,
    OpCode.INC: 4,
    OpCode.DEC: 4,
    OpCode.ADD: 8,
    OpCode.SUB: 8,
    OpCode.MUL: 8,
    OpCode.DIV: 8,
    OpCode.MOD: 8,
    OpCode.POW: 64,
    OpCode.SQRT: 64,
    OpCode.MODMUL: 32,
    OpCode.MODPOW: 2048,
    OpCode.SHL: 8,
    OpCode.SHR: 8,
    OpCode.NOT: 4,
    OpCode.BOOLAND: 8,
    OpCode.BOOLOR: 8,
    OpCode.NZ: 4,
    OpCode.NUMEQUAL: 8,
    OpCode.NUMNOTEQUAL: 8,
    OpCode.LT: 8,
    OpCode.LE: 8,
    OpCode.GT: 8,
    OpCode.GE: 8,
    OpCode.MIN: 8,
    OpCode.MAX: 8,
    OpCode.WITHIN: 8,
    # endregion

    # region Compound (0xBE-0xD4)
    OpCode.PACKMAP: 2048,
    OpCode.PACKSTRUCT: 2048,
    OpCode.PACK: 2048,
    OpCode.UNPACK: 2048,
    OpCode.NEWARRAY0: 16,
    OpCode.NEWARRAY: 512,
    OpCode.NEWARRAY_T: 512,
    OpCode.NEWSTRUCT0: 16,
    OpCode.NEWSTRUCT: 512,
    OpCode.NEWMAP: 8,
    OpCode.SIZE: 4,
    OpCode.HASKEY: 64,
    OpCode.KEYS: 16,
    OpCode.VALUES: 8192,
    OpCode.PICKITEM: 64,
    OpCode.APPEND: 8192,
    OpCode.SETITEM: 8192,
    OpCode.REVERSEITEMS: 8192,
    OpCode.REMOVE: 16,
    OpCode.CLEARITEMS: 16,
    OpCode.POPITEM: 16,
    # endregion

    # region Types (0xD8-0xE1)
    OpCode.ISNULL: 2,
    OpCode.ISTYPE: 2,
    OpCode.CONVERT: 8192,
    OpCode.ABORTMSG: 0,
    OpCode.ASSERTMSG: 1,
    # endregion
}


def get_price(opcode: int) -> int:
    """Get the base gas price for an opcode.

    Returns 0 for unknown opcodes (they will fault during execution).
    """
    try:
        op = OpCode(opcode)
    except ValueError:
        return 0
    return OPCODE_PRICE.get(op, 0)
