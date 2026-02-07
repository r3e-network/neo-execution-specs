# Neo v3.9.1 Protocol Verification Checklist Template

This checklist follows the execution-spec-tests style used by Ethereum: each checklist item must be tied to concrete vectors or documented external verification evidence.

| ID | Description | Status | Evidence |
| --- | --- | --- | --- |
| `general/line_coverage/python_spec` | Run Python spec tests with line coverage for protocol logic. | | |
| `general/test_coverage/vector_suite` | Validate runnable vectors against the Python VM implementation. | | |
| `general/fixture_integrity/vector_hashes` | Verify fixture integrity and deterministic vector corpus. | | |
| `general/diff/csharp_rpc` | Validate vectors against Neo C# reference endpoint. | | |
| `general/diff/neogo_rpc` | Validate vectors against NeoGo endpoint. | | |
| `vm/constants/push_variants` | Cover PUSH constants and null/boolean variants. | | |
| `vm/constants/pushdata_encodings` | Cover PUSHDATA1/PUSHDATA2/PUSHDATA4 encodings. | | |
| `vm/arithmetic/signed_edges` | Cover signed arithmetic edge cases and negative operands. | | |
| `vm/bitwise/signed_behavior` | Cover signed bitwise behavior and arithmetic shifts. | | |
| `vm/comparison/boundary_semantics` | Cover comparison boundary semantics (inclusive/exclusive). | | |
| `vm/control_flow/branch_paths` | Cover control-flow branch and return paths. | | |
| `vm/slot/local_and_arg_access` | Cover local slot store/load behavior. | | |
| `vm/splice/buffer_edges` | Cover splice operations with edge lengths and empty segments. | | |
| `vm/types/conversion_and_typechecks` | Cover type checks and conversion semantics. | | |
| `vm/compound/array_map_mutation` | Cover array/map mutation operations. | | |
| `vm/compound/map_introspection` | Cover map key/value introspection and access checks. | | |
| `native/neotoken/read_methods` | Cover NeoToken read-only methods. | | |
| `native/gastoken/read_methods` | Cover GasToken read-only methods. | | |
| `native/policy/mainnet_v391_values` | Validate Policy contract values for Neo v3.9.1 mainnet semantics. | | |
| `native/stdlib/string_and_memory_methods` | Cover StdLib string, base conversion, and memory compare behavior. | | |
| `native/cryptolib/hash_and_murmur` | Cover CryptoLib hash and Murmur32 methods. | | |
| `crypto/hash/sha256` | Cover SHA256 vectors across representative inputs. | | |
| `crypto/hash/ripemd160` | Cover RIPEMD160 vectors across representative inputs. | | |
| `crypto/hash/hash160` | Cover HASH160 vectors across representative inputs. | | |
| `crypto/hash/hash256` | Cover HASH256 vectors across representative inputs. | | |
| `cross_client/report_delta_zero` | Enforce zero vector delta between C# and NeoGo reports. | | |
