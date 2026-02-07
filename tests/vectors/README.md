# Neo Test Vectors

This directory contains test vectors for validating Neo VM implementations.

## Structure

```
tests/vectors/
├── vm/                    # VM instruction vectors
│   ├── arithmetic.json    # ADD, SUB, MUL, DIV, MOD, etc.
│   ├── stack.json         # PUSH, DUP, DROP, SWAP, etc.
│   ├── bitwise.json       # AND, OR, XOR, SHL, SHR
│   ├── comparison.json    # LT, LE, GT, GE, MIN, MAX
│   ├── boolean.json       # NOT, BOOLAND, BOOLOR, NZ
│   ├── compound.json      # Arrays, Maps, Structs
│   └── protocol_extended.json # Extended constants/data/map edge cases
├── crypto/                # Cryptographic operation vectors
│   ├── hash.json          # Core SHA256, RIPEMD160, Hash160, Hash256
│   ├── hash_extended.json # Extended hash coverage across inputs
│   └── bls12_381.json     # BLS12-381 curve operations
├── native/                # Native contract vectors
│   ├── neo_token.json     # NeoToken contract
│   ├── gas_token.json     # GasToken contract
│   └── native_extended.json # Extended StdLib/CryptoLib coverage
└── state/                 # State transition vectors
    └── state_transitions.json
```

## Vector Format

### VM Vectors
```json
{
  "name": "ADD_basic",
  "description": "Basic addition: 3 + 5 = 8",
  "pre": { "stack": [] },
  "script": "0x13159e",
  "post": { "stack": [8] },
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
  "input": { "data": "0x68656c6c6f" },
  "output": { "hash": "0x2cf24dba..." }
}
```

## Current Coverage

- Raw vectors on disk: `242`
- Runnable by `neo-diff`: `236` (BLS + state placeholder vectors are intentionally skipped)
- VM vectors: `182`
- Native vectors: `29`
- Crypto hash vectors: `25`

## Usage

### Generate Vectors
```bash
python tests/vectors/generate_all.py --verify
```

### Validate Against VM
```bash
python tests/vectors/validate.py
```

## Adding New Vectors

1. Create or edit a generator in `*_generator.py`
2. Add vectors using the appropriate dataclass
3. Run `generate_all.py` to regenerate JSON files
4. Run `validate.py` to verify correctness

## Scripts

| Script | Description |
|--------|-------------|
| `generator.py` | Core dataclasses and utilities |
| `generate_all.py` | Main generation script |
| `validate.py` | Validates VM vectors against implementation |
| `vm_generator.py` | VM arithmetic vectors |
| `stack_generator.py` | Stack manipulation vectors |
| `bitwise_generator.py` | Bitwise operation vectors |
| `comparison_generator.py` | Comparison vectors |
| `boolean_generator.py` | Boolean operation vectors |
| `compound_generator.py` | Compound type vectors |
| `crypto_generator.py` | Hash function vectors |
| `bls_generator.py` | BLS12-381 vectors |
| `native_generator.py` | Native contract vectors |
| `state_generator.py` | State transition vectors |
