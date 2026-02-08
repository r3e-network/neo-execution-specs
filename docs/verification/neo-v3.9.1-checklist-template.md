# Neo v3.9.1 Protocol Verification Checklist Template

This checklist follows the execution-spec-tests style used by Ethereum: each checklist item must be tied to concrete vectors or documented external verification evidence.

| ID | Description | Status | Evidence |
| --- | --- | --- | --- |
| `general/line_coverage/python_spec` | Validate general / line coverage / python spec. | | |
| `general/unit_suite/full_regression` | Validate general / unit suite / full regression. | | |
| `general/test_coverage/vector_suite` | Validate general / test coverage / vector suite. | | |
| `general/fixture_integrity/vector_hashes` | Validate general / fixture integrity / vector hashes. | | |
| `general/protocol_settings/mainnet_testnet_v391` | Validate general / protocol settings / mainnet testnet v391. | | |
| `general/hardfork/faun_activation` | Validate general / hardfork / faun activation. | | |
| `general/tooling/t8n_state_transition` | Validate general / tooling / t8n state transition. | | |
| `general/diff/csharp_rpc` | Validate general / diff / csharp rpc. | | |
| `general/diff/neogo_rpc` | Validate general / diff / neogo rpc. | | |
| `general/diff/neo_rs_rpc` | Validate general / diff / neo rs rpc. | | |
| `general/vector_corpus/deep_thresholds` | Validate general / vector corpus / deep thresholds. | | |
| `general/vector_corpus/opcode_surface_floor_deep` | Validate general / vector corpus / opcode surface floor deep. | | |
| `general/vector_quality/non_vm_expected_results` | Validate general / vector quality / non vm expected results. | | |
| `vm/constants/push_variants` | Cover vm / constants / push variants. | | |
| `vm/constants/pushdata_encodings` | Cover vm / constants / pushdata encodings. | | |
| `vm/stack/stack_manipulation` | Cover vm / stack / stack manipulation. | | |
| `vm/arithmetic/signed_edges` | Cover vm / arithmetic / signed edges. | | |
| `vm/bitwise/signed_behavior` | Cover vm / bitwise / signed behavior. | | |
| `vm/boolean/logic_semantics` | Cover vm / boolean / logic semantics. | | |
| `vm/comparison/boundary_semantics` | Cover vm / comparison / boundary semantics. | | |
| `vm/control_flow/branch_paths` | Cover vm / control flow / branch paths. | | |
| `vm/control_flow/abort_assert_throw_faults` | Cover vm / control flow / abort assert throw faults. | | |
| `vm/control_flow/long_and_relational_jump_variants` | Cover vm / control flow / long and relational jump variants. | | |
| `vm/control_flow/call_and_pointer_variants` | Cover vm / control flow / call and pointer variants. | | |
| `vm/slot/local_and_arg_access` | Cover vm / slot / local and arg access. | | |
| `vm/slot/static_argument_slot_fault_paths` | Cover vm / slot / static argument slot fault paths. | | |
| `vm/splice/buffer_edges` | Cover vm / splice / buffer edges. | | |
| `vm/splice/memcpy_success_and_boundaries` | Cover vm / splice / memcpy success and boundaries. | | |
| `vm/types/conversion_and_typechecks` | Cover vm / types / conversion and typechecks. | | |
| `vm/types/abortmsg_assertmsg_paths` | Cover vm / types / abortmsg assertmsg paths. | | |
| `vm/compound/array_map_mutation` | Cover vm / compound / array map mutation. | | |
| `vm/compound/map_introspection` | Cover vm / compound / map introspection. | | |
| `vm/compound/typed_array_pack_unpack_variants` | Cover vm / compound / typed array pack unpack variants. | | |
| `vm/runtime/callt_tokens` | Cover vm / runtime / callt tokens. | | |
| `vm/runtime/gas_accounting_v391` | Cover vm / runtime / gas accounting v391. | | |
| `vm/runtime/exception_handling` | Cover vm / runtime / exception handling. | | |
| `vm/runtime/try_catch_finally_long_offsets` | Cover vm / runtime / try catch finally long offsets. | | |
| `vm/runtime/reference_counter_and_limits` | Cover vm / runtime / reference counter and limits. | | |
| `vm/faults/divide_and_mod_zero` | Cover vm / faults / divide and mod zero. | | |
| `vm/faults/stack_index_and_underflow` | Cover vm / faults / stack index and underflow. | | |
| `vm/faults/splice_and_compound_invalid_args` | Cover vm / faults / splice and compound invalid args. | | |
| `crypto/hash/sha256` | Cover crypto / hash / sha256. | | |
| `crypto/hash/ripemd160` | Cover crypto / hash / ripemd160. | | |
| `crypto/hash/hash160` | Cover crypto / hash / hash160. | | |
| `crypto/hash/hash256` | Cover crypto / hash / hash256. | | |
| `crypto/hash/extended_input_classes` | Cover crypto / hash / extended input classes. | | |
| `crypto/hash/payload_matrix` | Cover crypto / hash / payload matrix. | | |
| `crypto/ecc/secp256r1_point_ops` | Cover crypto / ecc / secp256r1 point ops. | | |
| `crypto/ecdsa/sign_verify` | Cover crypto / ecdsa / sign verify. | | |
| `crypto/ed25519/sign_verify` | Cover crypto / ed25519 / sign verify. | | |
| `crypto/bls12_381/group_ops` | Cover crypto / bls12 381 / group ops. | | |
| `crypto/merkle/proof_verification` | Cover crypto / merkle / proof verification. | | |
| `crypto/bloom/filter_and_murmur` | Cover crypto / bloom / filter and murmur. | | |
| `contract/nef/serialization` | Cover contract / nef / serialization. | | |
| `contract/manifest/abi_permissions` | Cover contract / manifest / abi permissions. | | |
| `smartcontract/application_engine/lifecycle` | Cover smartcontract / application engine / lifecycle. | | |
| `smartcontract/interop/runtime_syscalls` | Cover smartcontract / interop / runtime syscalls. | | |
| `smartcontract/interop/storage_syscalls` | Cover smartcontract / interop / storage syscalls. | | |
| `smartcontract/interop/contract_syscalls` | Cover smartcontract / interop / contract syscalls. | | |
| `smartcontract/interop/crypto_syscalls` | Cover smartcontract / interop / crypto syscalls. | | |
| `smartcontract/syscalls/v391_metadata_and_flags` | Cover smartcontract / syscalls / v391 metadata and flags. | | |
| `smartcontract/serialization/binary_json` | Cover smartcontract / serialization / binary json. | | |
| `native/neotoken/read_methods` | Cover native / neotoken / read methods. | | |
| `native/neotoken/stateful_behaviors` | Cover native / neotoken / stateful behaviors. | | |
| `native/gastoken/read_methods` | Cover native / gastoken / read methods. | | |
| `native/gastoken/stateful_behaviors` | Cover native / gastoken / stateful behaviors. | | |
| `native/policy/mainnet_v391_values` | Cover native / policy / mainnet v391 values. | | |
| `native/stdlib/radix_and_encoding_edges` | Cover native / stdlib / radix and encoding edges. | | |
| `native/stdlib/memory_compare_binary_edges` | Cover native / stdlib / memory compare binary edges. | | |
| `native/stdlib/base64_and_memory_matrix` | Cover native / stdlib / base64 and memory matrix. | | |
| `native/cryptolib/hash_and_seed_edges` | Cover native / cryptolib / hash and seed edges. | | |
| `native/cryptolib/murmur_seed_matrix` | Cover native / cryptolib / murmur seed matrix. | | |
| `native/contractmanagement/lifecycle` | Cover native / contractmanagement / lifecycle. | | |
| `native/ledger/query_methods` | Cover native / ledger / query methods. | | |
| `native/oracle/request_response` | Cover native / oracle / request response. | | |
| `native/rolemanagement/designation` | Cover native / rolemanagement / designation. | | |
| `native/stdlib/string_and_memory_methods` | Cover native / stdlib / string and memory methods. | | |
| `native/cryptolib/hash_and_murmur` | Cover native / cryptolib / hash and murmur. | | |
| `native/notary/deposit_withdraw` | Cover native / notary / deposit withdraw. | | |
| `native/fungible/common_behavior` | Cover native / fungible / common behavior. | | |
| `network/payloads/block_header_serialization` | Cover network / payloads / block header serialization. | | |
| `network/payloads/transaction_signer_witness` | Cover network / payloads / transaction signer witness. | | |
| `network/payloads/witness_condition_scope` | Cover network / payloads / witness condition scope. | | |
| `network/io/binary_read_write` | Cover network / io / binary read write. | | |
| `persistence/datacache_snapshot_store` | Cover persistence / datacache snapshot store. | | |
| `ledger/blockchain_and_verifiers` | Cover ledger / blockchain and verifiers. | | |
| `ledger/mempool_policies` | Cover ledger / mempool policies. | | |
| `wallets/keypair_and_nep6` | Cover wallets / keypair and nep6. | | |
| `types/uint_and_biginteger` | Cover types / uint and biginteger. | | |
| `types/ecpoint_serialization` | Cover types / ecpoint serialization. | | |
| `state/transaction_script_execution_vectors` | Cover state / transaction script execution vectors. | | |
| `state/transaction_script_execution_deep_vectors` | Cover state / transaction script execution deep vectors. | | |
| `cross_client/report_delta_zero_csharp_neogo` | Enforce cross-client parity for report delta zero csharp neogo. | | |
| `cross_client/report_delta_zero_csharp_neo_rs` | Enforce cross-client parity for report delta zero csharp neo rs. | | |
| `cross_client/report_delta_zero_neogo_neo_rs` | Enforce cross-client parity for report delta zero neogo neo rs. | | |
| `cross_client/protocol_parity_getversion` | Enforce cross-client parity for protocol parity getversion. | | |
| `cross_client/triplet/mainnet_strict` | Enforce cross-client parity for triplet mainnet strict. | | |
| `cross_client/triplet/testnet_strict` | Enforce cross-client parity for triplet testnet strict. | | |
