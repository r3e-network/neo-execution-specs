#!/usr/bin/env python3
"""Comparison and Boolean Instruction Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neo.vm.opcode import OpCode
from generator import VMVector, VectorCollection, VectorCategory, script_to_hex
from vm_generator import push_int, build_script


def generate_comparison_vectors() -> VectorCollection:
    """Generate comparison instruction test vectors."""
    collection = VectorCollection(
        name="comparison",
        description="Comparison instruction test vectors (LT, LE, GT, GE, etc.)",
        category=VectorCategory.VM
    )
    
    # LT tests
    collection.add(VMVector(
        name="LT_true",
        description="Less than true: 3 < 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(5), OpCode.LT)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="LT_false",
        description="Less than false: 5 < 3",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(3), OpCode.LT)),
        post={"stack": [0]}
    ))
    
    collection.add(VMVector(
        name="LT_equal",
        description="Less than equal: 5 < 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(5), OpCode.LT)),
        post={"stack": [0]}
    ))
    
    # LE tests
    collection.add(VMVector(
        name="LE_less",
        description="Less or equal (less): 3 <= 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(5), OpCode.LE)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="LE_equal",
        description="Less or equal (equal): 5 <= 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(5), OpCode.LE)),
        post={"stack": [1]}
    ))
    
    # GT tests
    collection.add(VMVector(
        name="GT_true",
        description="Greater than true: 5 > 3",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(3), OpCode.GT)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="GT_false",
        description="Greater than false: 3 > 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(5), OpCode.GT)),
        post={"stack": [0]}
    ))
    
    # GE tests
    collection.add(VMVector(
        name="GE_greater",
        description="Greater or equal (greater): 5 >= 3",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(3), OpCode.GE)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="GE_equal",
        description="Greater or equal (equal): 5 >= 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(5), OpCode.GE)),
        post={"stack": [1]}
    ))
    
    # NUMEQUAL tests
    collection.add(VMVector(
        name="NUMEQUAL_true",
        description="Numeric equal true: 5 == 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(5), OpCode.NUMEQUAL)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="NUMEQUAL_false",
        description="Numeric equal false: 5 == 3",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(3), OpCode.NUMEQUAL)),
        post={"stack": [0]}
    ))
    
    # MIN/MAX tests
    collection.add(VMVector(
        name="MIN_basic",
        description="Minimum: min(3, 5) = 3",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(5), OpCode.MIN)),
        post={"stack": [3]}
    ))
    
    collection.add(VMVector(
        name="MAX_basic",
        description="Maximum: max(3, 5) = 5",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(3), push_int(5), OpCode.MAX)),
        post={"stack": [5]}
    ))
    
    # WITHIN tests
    collection.add(VMVector(
        name="WITHIN_true",
        description="Within range: 5 in [3, 7)",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(5), push_int(3), push_int(7), OpCode.WITHIN)),
        post={"stack": [1]}
    ))
    
    collection.add(VMVector(
        name="WITHIN_false_low",
        description="Below range: 2 in [3, 7)",
        pre={"stack": []},
        script=script_to_hex(build_script(push_int(2), push_int(3), push_int(7), OpCode.WITHIN)),
        post={"stack": [0]}
    ))
    
    return collection
