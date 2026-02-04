#!/usr/bin/env python3
"""Stack Instruction Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neo.vm.opcode import OpCode
from generator import VMVector, VectorCollection, VectorCategory, script_to_hex
from vm_generator import push_int, build_script


def generate_stack_vectors() -> VectorCollection:
    """Generate stack manipulation test vectors."""
    collection = VectorCollection(
        name="stack",
        description="Stack manipulation instruction test vectors",
        category=VectorCategory.VM
    )
    
    # PUSH tests
    collection.add(VMVector(
        name="PUSH0",
        description="Push 0 onto stack",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.PUSH0])),
        post={"stack": [0]}
    ))
    
    collection.add(VMVector(
        name="PUSH1",
        description="Push 1 onto stack",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.PUSH1])),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="PUSH16",
        description="Push 16 onto stack",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.PUSH16])),
        post={"stack": [16]}
    ))
    
    collection.add(VMVector(
        name="PUSHM1",
        description="Push -1 onto stack",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.PUSHM1])),
        post={"stack": [-1]}
    ))
    
    # DUP test
    collection.add(VMVector(
        name="DUP_basic",
        description="Duplicate top stack item",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.DUP)),
        post={"stack": [5, 5]}
    ))
    
    # DROP test
    collection.add(VMVector(
        name="DROP_basic",
        description="Drop top stack item",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), OpCode.DROP)),
        post={"stack": [1]}
    ))
    
    # SWAP test
    collection.add(VMVector(
        name="SWAP_basic",
        description="Swap top two items",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), OpCode.SWAP)),
        post={"stack": [2, 1]}
    ))
    
    # OVER test
    collection.add(VMVector(
        name="OVER_basic",
        description="Copy second item to top",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), OpCode.OVER)),
        post={"stack": [1, 2, 1]}
    ))
    
    # ROT test
    collection.add(VMVector(
        name="ROT_basic",
        description="Rotate top 3 items",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), push_int(3), OpCode.ROT)),
        post={"stack": [2, 3, 1]}
    ))
    
    # NIP test
    collection.add(VMVector(
        name="NIP_basic",
        description="Remove second item",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), OpCode.NIP)),
        post={"stack": [2]}
    ))
    
    # TUCK test
    collection.add(VMVector(
        name="TUCK_basic",
        description="Copy top item below second",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), OpCode.TUCK)),
        post={"stack": [2, 1, 2]}
    ))
    
    # DEPTH test
    collection.add(VMVector(
        name="DEPTH_empty",
        description="Depth of empty stack",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.DEPTH])),
        post={"stack": [0]}
    ))
    
    collection.add(VMVector(
        name="DEPTH_three",
        description="Depth of 3-item stack",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), push_int(3), OpCode.DEPTH)),
        post={"stack": [1, 2, 3, 3]}
    ))
    
    # CLEAR test
    collection.add(VMVector(
        name="CLEAR_basic",
        description="Clear entire stack",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), push_int(3), OpCode.CLEAR)),
        post={"stack": []}
    ))
    
    # REVERSE3 test
    collection.add(VMVector(
        name="REVERSE3_basic",
        description="Reverse top 3 items",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), push_int(3), OpCode.REVERSE3)),
        post={"stack": [3, 2, 1]}
    ))
    
    # REVERSE4 test
    collection.add(VMVector(
        name="REVERSE4_basic",
        description="Reverse top 4 items",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(2), push_int(3), push_int(4), OpCode.REVERSE4)),
        post={"stack": [4, 3, 2, 1]}
    ))
    
    return collection
