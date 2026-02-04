#!/usr/bin/env python3
"""Boolean Instruction Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neo.vm.opcode import OpCode
from generator import VMVector, VectorCollection, VectorCategory, script_to_hex
from vm_generator import push_int, build_script


def generate_boolean_vectors() -> VectorCollection:
    """Generate boolean instruction test vectors."""
    collection = VectorCollection(
        name="boolean",
        description="Boolean instruction test vectors (NOT, AND, OR, NZ)",
        category=VectorCategory.VM
    )
    
    # NOT tests
    collection.add(VMVector(
        name="NOT_true",
        description="NOT true = false",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), OpCode.NOT)),
        post={"stack": [0]}
    ))
    
    collection.add(VMVector(
        name="NOT_false",
        description="NOT false = true",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(0), OpCode.NOT)),
        post={"stack": [1]}
    ))
    
    # BOOLAND tests
    collection.add(VMVector(
        name="BOOLAND_true_true",
        description="true AND true = true",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(1), OpCode.BOOLAND)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="BOOLAND_true_false",
        description="true AND false = false",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(0), OpCode.BOOLAND)),
        post={"stack": [0]}
    ))
    
    collection.add(VMVector(
        name="BOOLAND_false_false",
        description="false AND false = false",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(0), push_int(0), OpCode.BOOLAND)),
        post={"stack": [0]}
    ))
    
    # BOOLOR tests
    collection.add(VMVector(
        name="BOOLOR_true_true",
        description="true OR true = true",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(1), OpCode.BOOLOR)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="BOOLOR_true_false",
        description="true OR false = true",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(1), push_int(0), OpCode.BOOLOR)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="BOOLOR_false_false",
        description="false OR false = false",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(0), push_int(0), OpCode.BOOLOR)),
        post={"stack": [0]}
    ))
    
    # NZ tests
    collection.add(VMVector(
        name="NZ_nonzero",
        description="NZ of nonzero = true",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), OpCode.NZ)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="NZ_zero",
        description="NZ of zero = false",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(0), OpCode.NZ)),
        post={"stack": [0]}
    ))
    
    return collection
