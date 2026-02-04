#!/usr/bin/env python3
"""Bitwise Instruction Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neo.vm.opcode import OpCode
from generator import VMVector, VectorCollection, VectorCategory, script_to_hex
from vm_generator import push_int, build_script


def generate_bitwise_vectors() -> VectorCollection:
    """Generate bitwise instruction test vectors."""
    collection = VectorCollection(
        name="bitwise",
        description="Bitwise instruction test vectors (AND, OR, XOR, etc.)",
        category=VectorCategory.VM
    )
    
    # AND tests
    collection.add(VMVector(
        name="AND_basic",
        description="Bitwise AND: 12 & 10 = 8",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(12), push_int(10), OpCode.AND)),
        post={"stack": [8]}
    ))
    
    collection.add(VMVector(
        name="AND_zero",
        description="AND with zero: 15 & 0 = 0",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(15), push_int(0), OpCode.AND)),
        post={"stack": [0]}
    ))
    
    # OR tests
    collection.add(VMVector(
        name="OR_basic",
        description="Bitwise OR: 12 | 10 = 14",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(12), push_int(10), OpCode.OR)),
        post={"stack": [14]}
    ))
    
    collection.add(VMVector(
        name="OR_zero",
        description="OR with zero: 15 | 0 = 15",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(15), push_int(0), OpCode.OR)),
        post={"stack": [15]}
    ))
    
    # XOR tests
    collection.add(VMVector(
        name="XOR_basic",
        description="Bitwise XOR: 12 ^ 10 = 6",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(12), push_int(10), OpCode.XOR)),
        post={"stack": [6]}
    ))
    
    collection.add(VMVector(
        name="XOR_same",
        description="XOR same value: 15 ^ 15 = 0",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(15), push_int(15), OpCode.XOR)),
        post={"stack": [0]}
    ))
    
    # INVERT tests
    collection.add(VMVector(
        name="INVERT_zero",
        description="Bitwise NOT: ~0 = -1",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(0), OpCode.INVERT)),
        post={"stack": [-1]}
    ))
    
    # SHL tests
    collection.add(VMVector(
        name="SHL_basic",
        description="Shift left: 1 << 4 = 16",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(4), OpCode.SHL)),
        post={"stack": [16]}
    ))
    
    collection.add(VMVector(
        name="SHL_zero",
        description="Shift left by 0: 5 << 0 = 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(0), OpCode.SHL)),
        post={"stack": [5]}
    ))
    
    # SHR tests
    collection.add(VMVector(
        name="SHR_basic",
        description="Shift right: 16 >> 2 = 4",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(16), push_int(2), OpCode.SHR)),
        post={"stack": [4]}
    ))
    
    collection.add(VMVector(
        name="SHR_zero",
        description="Shift right by 0: 5 >> 0 = 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(0), OpCode.SHR)),
        post={"stack": [5]}
    ))
    
    return collection
