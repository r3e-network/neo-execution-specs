#!/usr/bin/env python3
"""VM Instruction Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neo.vm.opcode import OpCode
from generator import VMVector, VectorCollection, VectorCategory, script_to_hex


def push_int(n: int) -> list:
    """Generate PUSH opcode(s) for an integer."""
    if n == -1:
        return [OpCode.PUSHM1]
    elif 0 <= n <= 16:
        return [OpCode.PUSH0 + n]
    elif -128 <= n <= 127:
        # PUSHINT8
        return [OpCode.PUSHINT8, n & 0xFF]
    else:
        # For simplicity, use PUSHINT32 for larger values
        return [OpCode.PUSHINT32] + list(n.to_bytes(4, 'little', signed=True))


def build_script(*ops) -> bytes:
    """Build a script from opcodes and values."""
    result = []
    for op in ops:
        if isinstance(op, list):
            result.extend(op)
        else:
            result.append(op)
    return bytes(result)


def generate_arithmetic_vectors() -> VectorCollection:
    """Generate arithmetic instruction test vectors."""
    collection = VectorCollection(
        name="arithmetic",
        description="Arithmetic instruction test vectors (ADD, SUB, MUL, DIV, MOD, etc.)",
        category=VectorCategory.VM
    )
    
    # ADD tests
    collection.add(VMVector(
        name="ADD_basic",
        description="Basic addition: 3 + 5 = 8",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(5), OpCode.ADD)),
        post={"stack": [8]}
    ))
    
    collection.add(VMVector(
        name="ADD_negative",
        description="Addition with negative: 5 + (-3) = 2",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(-3), OpCode.ADD)),
        post={"stack": [2]}
    ))
    
    collection.add(VMVector(
        name="ADD_zero",
        description="Addition with zero: 7 + 0 = 7",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(7), push_int(0), OpCode.ADD)),
        post={"stack": [7]}
    ))
    
    # SUB tests
    collection.add(VMVector(
        name="SUB_basic",
        description="Basic subtraction: 7 - 3 = 4",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(7), push_int(3), OpCode.SUB)),
        post={"stack": [4]}
    ))
    
    collection.add(VMVector(
        name="SUB_negative_result",
        description="Subtraction with negative result: 3 - 7 = -4",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(7), OpCode.SUB)),
        post={"stack": [-4]}
    ))
    
    # MUL tests
    collection.add(VMVector(
        name="MUL_basic",
        description="Basic multiplication: 3 * 4 = 12",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(4), OpCode.MUL)),
        post={"stack": [12]}
    ))
    
    collection.add(VMVector(
        name="MUL_zero",
        description="Multiplication by zero: 5 * 0 = 0",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(0), OpCode.MUL)),
        post={"stack": [0]}
    ))
    
    collection.add(VMVector(
        name="MUL_negative",
        description="Multiplication with negative: 3 * (-4) = -12",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(-4), OpCode.MUL)),
        post={"stack": [-12]}
    ))
    
    # DIV tests
    collection.add(VMVector(
        name="DIV_basic",
        description="Basic division: 10 / 3 = 3 (integer)",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(10), push_int(3), OpCode.DIV)),
        post={"stack": [3]}
    ))
    
    collection.add(VMVector(
        name="DIV_exact",
        description="Exact division: 12 / 4 = 3",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(12), push_int(4), OpCode.DIV)),
        post={"stack": [3]}
    ))
    
    # MOD tests
    collection.add(VMVector(
        name="MOD_basic",
        description="Basic modulo: 10 % 3 = 1",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(10), push_int(3), OpCode.MOD)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="MOD_exact",
        description="Exact modulo: 12 % 4 = 0",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(12), push_int(4), OpCode.MOD)),
        post={"stack": [0]}
    ))
    
    # NEGATE tests
    collection.add(VMVector(
        name="NEGATE_positive",
        description="Negate positive: -5 = -5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.NEGATE)),
        post={"stack": [-5]}
    ))
    
    collection.add(VMVector(
        name="NEGATE_negative",
        description="Negate negative: -(-5) = 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(-5), OpCode.NEGATE)),
        post={"stack": [5]}
    ))
    
    # ABS tests
    collection.add(VMVector(
        name="ABS_positive",
        description="Absolute of positive: |5| = 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.ABS)),
        post={"stack": [5]}
    ))
    
    collection.add(VMVector(
        name="ABS_negative",
        description="Absolute of negative: |-5| = 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.NEGATE, OpCode.ABS)),
        post={"stack": [5]}
    ))
    
    # INC/DEC tests
    collection.add(VMVector(
        name="INC_basic",
        description="Increment: 5 + 1 = 6",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.INC)),
        post={"stack": [6]}
    ))
    
    collection.add(VMVector(
        name="DEC_basic",
        description="Decrement: 5 - 1 = 4",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.DEC)),
        post={"stack": [4]}
    ))
    
    # SIGN tests
    collection.add(VMVector(
        name="SIGN_positive",
        description="Sign of positive: sign(5) = 1",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.SIGN)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="SIGN_negative",
        description="Sign of negative: sign(-5) = -1",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.NEGATE, OpCode.SIGN)),
        post={"stack": [-1]}
    ))
    
    collection.add(VMVector(
        name="SIGN_zero",
        description="Sign of zero: sign(0) = 0",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(0), OpCode.SIGN)),
        post={"stack": [0]}
    ))
    
    return collection
