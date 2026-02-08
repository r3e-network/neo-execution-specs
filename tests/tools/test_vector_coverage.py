"""Coverage guards for execution-spec vector corpus."""

from __future__ import annotations

from pathlib import Path

from neo.vm.opcode import OpCode
from neo.tools.diff.runner import VectorLoader


def _category(vector) -> str:
    metadata = vector.metadata if isinstance(vector.metadata, dict) else {}
    return str(metadata.get("category", "vm")).lower()


def test_vector_corpus_minimum_counts() -> None:
    vectors = list(VectorLoader.load_directory(Path("tests/vectors")))

    assert len(vectors) >= 380

    vm_vectors = [v for v in vectors if _category(v) == "vm"]
    native_vectors = [v for v in vectors if _category(v) == "native"]
    crypto_vectors = [v for v in vectors if _category(v) == "crypto"]
    state_vectors = [v for v in vectors if _category(v) == "state"]

    assert len(vm_vectors) >= 250
    assert len(native_vectors) >= 60
    assert len(crypto_vectors) >= 55
    assert len(state_vectors) >= 8


def test_advanced_vm_opcode_coverage_floor() -> None:
    vm_vectors = [
        vector
        for vector in VectorLoader.load_directory(Path("tests/vectors/vm"))
        if _category(vector) == "vm"
    ]

    observed_opcodes: set[int] = set()
    for vector in vm_vectors:
        observed_opcodes.update(vector.script)

    required = {
        int(OpCode.PUSHA),
        int(OpCode.PUSHDATA2),
        int(OpCode.PUSHDATA4),
        int(OpCode.JMP_L),
        int(OpCode.JMPIF_L),
        int(OpCode.JMPIFNOT_L),
        int(OpCode.JMPEQ),
        int(OpCode.JMPEQ_L),
        int(OpCode.JMPNE),
        int(OpCode.JMPNE_L),
        int(OpCode.JMPGT),
        int(OpCode.JMPGT_L),
        int(OpCode.JMPGE),
        int(OpCode.JMPGE_L),
        int(OpCode.JMPLT),
        int(OpCode.JMPLT_L),
        int(OpCode.JMPLE),
        int(OpCode.JMPLE_L),
        int(OpCode.CALL),
        int(OpCode.CALL_L),
        int(OpCode.CALLA),
        int(OpCode.ABORT),
        int(OpCode.ASSERT),
        int(OpCode.THROW),
        int(OpCode.TRY),
        int(OpCode.TRY_L),
        int(OpCode.ENDTRY),
        int(OpCode.ENDTRY_L),
        int(OpCode.ENDFINALLY),
        int(OpCode.INITSSLOT),
        int(OpCode.LDSFLD0),
        int(OpCode.STSFLD0),
        int(OpCode.LDARG0),
        int(OpCode.STARG0),
        int(OpCode.MEMCPY),
        int(OpCode.DIV),
        int(OpCode.MOD),
        int(OpCode.PACK),
        int(OpCode.PACKSTRUCT),
        int(OpCode.PACKMAP),
        int(OpCode.UNPACK),
        int(OpCode.NEWARRAY_T),
        int(OpCode.NEWSTRUCT),
        int(OpCode.SETITEM),
        int(OpCode.REMOVE),
        int(OpCode.CLEARITEMS),
        int(OpCode.POPITEM),
        int(OpCode.KEYS),
        int(OpCode.VALUES),
        int(OpCode.XDROP),
        int(OpCode.ROLL),
        int(OpCode.ABORTMSG),
        int(OpCode.ASSERTMSG),
    }

    assert required.issubset(observed_opcodes)
