# Neo Test Vectors

This directory contains protocol-level vectors for validating Neo N3 execution behavior across implementations.

## Structure

```
tests/vectors/
├── vm/                              # VM instruction and fault vectors
│   ├── arithmetic.json
│   ├── bitwise.json
│   ├── boolean.json
│   ├── comparison.json
│   ├── compound.json
│   ├── control_flow.json
│   ├── control_flow_deep.json       # Long jumps, call variants, TRY/ENDTRY paths
│   ├── faults_extended.json         # Fault-path boundaries and invalid arguments
│   ├── memory_slot_compound_deep.json # MEMCPY, slot lifecycle, typed array/pack paths
│   ├── protocol_extended.json
│   ├── slot.json
│   ├── splice.json
│   ├── stack.json
│   └── types.json
├── crypto/                          # Cryptographic operation vectors
│   ├── hash.json
│   ├── hash_extended.json
│   ├── hash_deep.json
│   ├── hash_matrix.json             # Payload-length and entropy matrix
│   └── bls12_381.json               # BLS vectors (tracked; runtime unsupported in neo-diff)
├── native/                          # Native contract vectors
│   ├── gas_token.json
│   ├── native_extended.json
│   ├── native_deep.json
│   ├── native_matrix.json           # StdLib/CryptoLib radix/base64/seed matrix
│   └── neo_token.json
└── state/                           # State-transition vectors
    ├── executable_state_stubs.json
    ├── executable_state_deep.json
    └── state_transitions.json       # Placeholder non-executable transition schema
```

## Vector Format

### VM Vectors
```json
{
  "name": "ADD_basic",
  "description": "Basic addition: 3 + 5 = 8",
  "pre": {"stack": []},
  "script": "0x13159e",
  "post": {"stack": [8]},
  "error": null,
  "gas": null
}
```

### Crypto Vectors
```json
{
  "name": "SHA256_hello",
  "description": "SHA256 of 'hello'",
  "operation": "SHA256",
  "input": {"data": "0x68656c6c6f"},
  "output": {"hash": "0x2cf24dba..."}
}
```

## Current Coverage

- Raw vectors on disk: `399`
- Runnable by `neo-diff`: `393` (BLS + placeholder state vector intentionally skipped)
- VM vectors: `262`
- Native vectors: `66`
- Crypto vectors (supported operations): `57`
- Script-backed state vectors: `8`

## Usage

### Protocol Checklist Coverage
```bash
neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md \
             --coverage-manifest tests/vectors/checklist_coverage.json \
             --vectors-root tests/vectors/
```

### Generate Vectors
```bash
python tests/vectors/generate_all.py --verify
```

### Validate Against VM
```bash
python tests/vectors/validate.py
```

## Adding New Vectors

1. Add or update vectors in the appropriate JSON suite (or generator for generated suites).
2. Run `python tests/vectors/validate.py` for VM-vector correctness.
3. Run checklist coverage and tooling tests:
   - `neo-coverage ...`
   - `pytest tests/tools/test_vector_coverage.py -q`
   - `pytest tests/tools/test_non_vm_vector_expectations.py -q`
4. Map new vectors to checklist IDs in `tests/vectors/checklist_coverage.json`.

## Scripts

| Script | Description |
|--------|-------------|
| `generator.py` | Core dataclasses and utilities |
| `generate_all.py` | Main generation script |
| `validate.py` | Validates VM vectors against implementation |
| `*_generator.py` | Category-specific vector generators |
| `checklist_coverage.json` | Checklist ID -> vector/evidence mapping |
