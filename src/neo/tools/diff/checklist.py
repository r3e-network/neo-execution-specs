"""Neo protocol verification checklist identifiers."""

from __future__ import annotations

NEO_V391_CHECKLIST_IDS: tuple[str, ...] = (
    "general/line_coverage/python_spec",
    "general/test_coverage/vector_suite",
    "general/fixture_integrity/vector_hashes",
    "general/diff/csharp_rpc",
    "general/diff/neogo_rpc",
    "vm/constants/push_variants",
    "vm/constants/pushdata_encodings",
    "vm/arithmetic/signed_edges",
    "vm/bitwise/signed_behavior",
    "vm/comparison/boundary_semantics",
    "vm/control_flow/branch_paths",
    "vm/slot/local_and_arg_access",
    "vm/splice/buffer_edges",
    "vm/types/conversion_and_typechecks",
    "vm/compound/array_map_mutation",
    "vm/compound/map_introspection",
    "native/neotoken/read_methods",
    "native/gastoken/read_methods",
    "native/policy/mainnet_v391_values",
    "native/stdlib/string_and_memory_methods",
    "native/cryptolib/hash_and_murmur",
    "crypto/hash/sha256",
    "crypto/hash/ripemd160",
    "crypto/hash/hash160",
    "crypto/hash/hash256",
    "cross_client/report_delta_zero",
)
