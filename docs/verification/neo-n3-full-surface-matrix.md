# Neo N3 Full-Surface Verification Matrix (Ethereum-Style)

This matrix expands Neo execution-spec verification from VM-heavy coverage to full Neo N3 protocol surface, mirroring Ethereum execution-spec-tests methodology.

## Scope

- Protocol settings and hardfork activation gates.
- NeoVM opcode semantics, gas accounting, limits, and exception behavior.
- Smart contract engine, interop syscall metadata, and serialization.
- Native contracts (NEO/GAS/Policy/ContractManagement/Ledger/Oracle/Role/StdLib/CryptoLib/Notary).
- Cryptography stack (hashing, ECC, ECDSA, Ed25519, BLS, Merkle, Bloom/Murmur).
- Network payload serialization and binary I/O compatibility.
- Persistence, ledger validation paths, wallets, and core types.
- Cross-client differential checks across Neo v3.9.1 C#, NeoGo, and neo-rs.

## Enforcement Model

- Source of truth IDs: `src/neo/tools/diff/checklist.py`.
- Human-readable template: `docs/verification/neo-v3.9.1-checklist-template.md`.
- Coverage manifest: `tests/vectors/checklist_coverage.json`.
- Gate command: `neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md --coverage-manifest tests/vectors/checklist_coverage.json --vectors-root tests/vectors/`.

## Tri-Client Validation

- Pairwise C# vs NeoGo: `neo-compat`.
- Three-way C# vs NeoGo vs neo-rs: `neo-multicompat`.
- The three cross-client checklist IDs remain required coverage gates.
