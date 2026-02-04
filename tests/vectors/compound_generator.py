#!/usr/bin/env python3
"""Compound Type Instruction Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neo.vm.opcode import OpCode
from generator import VMVector, VectorCollection, VectorCategory, script_to_hex
from vm_generator import push_int, build_script


def generate_compound_vectors() -> VectorCollection:
    """Generate compound type instruction test vectors."""
    collection = VectorCollection(
        name="compound",
        description="Compound type instruction test vectors (arrays, maps, structs)",
        category=VectorCategory.VM
    )
    
    # NEWARRAY0 test
    collection.add(VMVector(
        name="NEWARRAY0_basic",
        description="Create empty array",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.NEWARRAY0])),
        post={"stack": [{"type": "Array", "value": []}]}
    ))
    
    # NEWSTRUCT0 test
    collection.add(VMVector(
        name="NEWSTRUCT0_basic",
        description="Create empty struct",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.NEWSTRUCT0])),
        post={"stack": [{"type": "Struct", "value": []}]}
    ))
    
    # NEWMAP test
    collection.add(VMVector(
        name="NEWMAP_basic",
        description="Create empty map",
        pre={"stack": []},
        script=script_to_hex(bytes([OpCode.NEWMAP])),
        post={"stack": [{"type": "Map", "value": {}}]}
    ))
    
    # PACK test
    collection.add(VMVector(
        name="PACK_basic",
        description="Pack 3 items into array",
        pre={"stack": []},
        script=script_to_hex(build_script(
            push_int(1), push_int(2), push_int(3), push_int(3), OpCode.PACK
        )),
        post={"stack": [{"type": "Array", "value": [3, 2, 1]}]}
    ))
    
    return collection
