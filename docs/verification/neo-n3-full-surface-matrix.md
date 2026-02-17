# Neo N3 Full-Surface Verification Matrix (Ethereum-Style)

This matrix expands Neo execution-spec verification from VM-heavy coverage to full Neo N3 protocol surface, mirroring Ethereum execution-spec-tests methodology.

## Scope

- Protocol settings and hardfork activation gates.
- NeoVM opcode semantics, gas accounting, limits, exception behavior, and explicit fault-path assertions.
- Deep control-flow semantics (short/long jump families, call variants including pointer dispatch, TRY/ENDTRY long-offset paths).
- Deep splice/slot/compound semantics (MEMCPY bounds, static/arg slot lifecycle faults, typed arrays, pack/unpack variants).
- Smart contract engine, interop syscall metadata, and serialization.
- Native contracts (NEO/GAS/Policy/ContractManagement/Ledger/Oracle/Role/StdLib/CryptoLib/Notary/Treasury).
- Cryptography stack (hashing, ECC, ECDSA, Ed25519, BLS, Merkle, Bloom/Murmur) with payload-matrix vectors.
- Network payload serialization and binary I/O compatibility.
- Persistence, ledger validation paths, wallets, core types, and script-backed state vector execution.
- Cross-client differential checks across Neo v3.9.1 C#, NeoGo, and neo-rs.

## Enforcement Model

- Source of truth IDs: `src/neo/tools/diff/checklist.py`.
- Human-readable template: `docs/verification/neo-v3.9.1-checklist-template.md`.
- Coverage manifest: `tests/vectors/checklist_coverage.json`.
- Gate command: `neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md --coverage-manifest tests/vectors/checklist_coverage.json --vectors-root tests/vectors/`.

## Tri-Client Validation

- Pairwise C# vs NeoGo: `neo-compat`.
- Three-way C# vs NeoGo vs neo-rs: `neo-multicompat`.
- Public NeoGo endpoint drift probe automation: `python3 scripts/neogo_endpoint_matrix.py`.
- The cross-client checklist IDs remain required coverage gates.

## Depth Gates

- Vector depth gates are enforced in `tests/tools/test_vector_coverage.py` (total corpus + per-domain minimums + advanced opcode floor).
- Non-VM expected output integrity is enforced in `tests/tools/test_non_vm_vector_expectations.py`.
- VM deep suites are validated by `tests/vectors/validate.py` and consumed by diff tooling under `tests/vectors/vm/control_flow_deep.json` and `tests/vectors/vm/memory_slot_compound_deep.json`.
