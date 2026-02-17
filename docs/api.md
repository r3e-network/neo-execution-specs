# API Reference

This document covers the main APIs of neo-execution-specs.

For normative protocol profile and transition semantics, see
`docs/execution-spec.md`.

## Virtual Machine

### ExecutionEngine

The core VM that executes Neo scripts.

```python
from neo.vm import ExecutionEngine, VMState

# Create engine
engine = ExecutionEngine()

# Load and execute script
engine.load_script(script_bytes)
state = engine.execute()

# Check result
if state == VMState.HALT:
    result = engine.result_stack.pop()
    print(f"Result: {result.get_integer()}")
else:
    print(f"Execution failed: {engine.fault_exception}")
```

#### Methods

| Method | Description |
|--------|-------------|
| `load_script(script)` | Load script bytes for execution |
| `execute()` | Execute until completion |
| `step_out()` | Execute until current context returns |
| `push(item)` | Push item onto evaluation stack |
| `pop()` | Pop item from evaluation stack |
| `peek(index=0)` | Peek at stack item |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `state` | `VMState` | Current VM state |
| `result_stack` | `EvaluationStack` | Result stack after execution |
| `current_context` | `ExecutionContext` | Current execution context |
| `invocation_stack` | `list` | Stack of execution contexts |
| `fault_exception` | `str` | Exception message if faulted |

### ScriptBuilder

Build Neo VM scripts programmatically.

```python
from neo.vm import ScriptBuilder
from neo.vm.opcode import OpCode

sb = ScriptBuilder()

# Push values
sb.emit_push(100)           # Push integer
sb.emit_push(b"hello")      # Push bytes
sb.emit_push(True)          # Push boolean

# Emit opcodes
sb.emit(OpCode.ADD)
sb.emit(OpCode.NOP)

# Call contracts
sb.emit_syscall("System.Contract.Call")
sb.emit_call(offset=10)

# Get script bytes
script = sb.to_array()
```

#### Methods

| Method | Description |
|--------|-------------|
| `emit(opcode)` | Emit single opcode |
| `emit_push(value)` | Push value (auto-detects type) |
| `emit_call(offset)` | Emit CALL instruction |
| `emit_syscall(name)` | Emit SYSCALL instruction |
| `emit_jump(opcode, offset)` | Emit jump instruction |
| `to_array()` | Get script as bytes |

### Stack Items

All values on the VM stack are `StackItem` instances.

```python
from neo.vm.types import Integer, ByteString, Array, Map, Struct, Buffer

# Integer
i = Integer(42)
print(i.get_integer())  # 42
print(i.get_boolean())  # True

# ByteString
bs = ByteString(b"hello")
print(bs.get_bytes())   # b'hello'
print(bs.get_string())  # 'hello'

# Array
arr = Array([Integer(1), Integer(2), Integer(3)])
print(len(arr))         # 3
print(arr[0])           # Integer(1)

# Map
m = Map()
m[ByteString(b"key")] = Integer(100)
print(m[ByteString(b"key")])  # Integer(100)

# Struct (value-type array)
s = Struct([Integer(1), Integer(2)])
clone = s.clone()       # Deep copy
```

#### Type Hierarchy

```
StackItem (base)
├── PrimitiveType
│   ├── Boolean
│   ├── Integer
│   └── ByteString
├── CompoundType
│   ├── Array
│   ├── Struct
│   └── Map
├── Buffer
├── Pointer
└── InteropInterface
```

## Cryptography

### Hash Functions

```python
from neo.crypto import hash

# Single hash
sha256 = hash.sha256(b"data")
ripemd160 = hash.ripemd160(b"data")

# Double hash
hash256 = hash.hash256(b"data")  # SHA256(SHA256(data))
hash160 = hash.hash160(b"data")  # RIPEMD160(SHA256(data))

# Murmur3
from neo.crypto.murmur3 import murmur32
h = murmur32(b"data", seed=0)
```

### Elliptic Curves

```python
from neo.crypto.ecc import ECPoint, NamedCurve

# Create point from bytes
point = ECPoint.from_bytes(public_key_bytes, NamedCurve.SECP256R1)

# Point operations
encoded = point.encode_point(compressed=True)
is_valid = point.is_on_curve()
```

### ECDSA Signatures

```python
from neo.crypto.ecc import ECDSA, NamedCurve

# Verify signature
is_valid = ECDSA.verify(
    message=message_bytes,
    signature=signature_bytes,
    public_key=public_key_bytes,
    curve=NamedCurve.SECP256R1
)
```

## Native Contracts

### NeoToken

```python
from neo.native import NeoToken

neo = NeoToken()

# Get balance (requires ApplicationEngine context)
balance = neo.balance_of(snapshot, account_hash)

# Get committee
committee = neo.get_committee(snapshot)

# Get candidates
candidates = neo.get_candidates(snapshot)
```

### GasToken

```python
from neo.native import GasToken

gas = GasToken()

# Get balance
balance = gas.balance_of(snapshot, account_hash)

# Get decimals
decimals = gas.decimals  # 8
```

### PolicyContract

```python
from neo.native import PolicyContract

policy = PolicyContract()

# Get fees
fee_per_byte = policy.get_fee_per_byte(snapshot)
exec_fee_factor = policy.get_exec_fee_factor(snapshot)

# Check blocked accounts
is_blocked = policy.is_blocked(snapshot, account_hash)
```

### StdLib

```python
from neo.native import StdLib

stdlib = StdLib()

# Serialization
serialized = stdlib.serialize(stack_item)
deserialized = stdlib.deserialize(serialized)

# Encoding
base64 = stdlib.base64_encode(data)
base58 = stdlib.base58_encode(data)

# String operations
result = stdlib.string_split(text, separator)

# Hardfork-gated encoding helpers (require active protocol context)
base64url = stdlib.base64_url_encode("hello", context=engine)
hexed = stdlib.hex_encode(b"\xde\xad\xbe\xef", context=engine)
```

## Persistence

### MemoryStore

In-memory storage implementation.

```python
from neo.persistence import MemoryStore

store = MemoryStore()

# Basic operations
store.put(key, value)
value = store.get(key)
store.delete(key)

# Iteration
for key, value in store.seek(prefix):
    print(key, value)
```

### Snapshot

Isolated view of storage state.

```python
from neo.persistence import MemoryStore

store = MemoryStore()
snapshot = store.get_snapshot()

# Modifications are isolated
snapshot.put(b"key", b"value")

# Commit to persist
snapshot.commit()
```

## Types

### UInt160

20-byte hash, commonly used for addresses.

```python
from neo.types import UInt160

# From bytes
h = UInt160(bytes(20))

# From hex string
h = UInt160.from_string("0x0000000000000000000000000000000000000000")

# To string
print(str(h))  # "0x..."
```

### UInt256

32-byte hash, used for transaction and block hashes.

```python
from neo.types import UInt256

# From bytes
h = UInt256(bytes(32))

# Comparison
h1 == h2
h1 < h2
```

### BigInteger

Arbitrary precision integer with Neo-specific behavior.

```python
from neo.types import BigInteger

# Create
bi = BigInteger(12345678901234567890)

# From bytes (little-endian)
bi = BigInteger.from_bytes_le(b"\x01\x02\x03")

# To bytes
data = bi.to_bytes_le()

# Size limit (32 bytes max)
MAX_SIZE = 32
```

## CLI Tools

### neo-diff

Compare Python spec with C# implementation.

```bash
# Python-only mode
neo-diff -v tests/vectors/vm/ -p

# With C# comparison
neo-diff -v tests/vectors/ -r http://localhost:10332 -o report.json
```

### neo-compat

Run `neo-diff` against C# and NeoGo RPC endpoints, then compare reports.

```bash
neo-compat --vectors tests/vectors/ \
           --csharp-rpc http://seed1.neo.org:10332 \
           --neogo-rpc http://rpc3.n3.nspcc.ru:10332
```

### neo-multicompat

Run `neo-diff` against C#, NeoGo, and neo-rs endpoints, then compare pairwise deltas.

```bash
neo-multicompat --vectors tests/vectors/ \
                --csharp-rpc http://seed1.neo.org:10332 \
                --neogo-rpc http://rpc3.n3.nspcc.ru:10332 \
                --neo-rs-rpc http://127.0.0.1:40332
```

### Endpoint Matrix Helper

For repeatable public NeoGo endpoint drift probes against expected delta vectors:

```bash
python3 scripts/neogo_endpoint_matrix.py \
  --output-dir reports/compat-endpoint-matrix \
  --prefix neogo-0.116-endpoint-matrix
```

### neo-coverage

Validate protocol checklist coverage mappings against vector fixtures.

```bash
neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md \
             --coverage-manifest tests/vectors/checklist_coverage.json \
             --vectors-root tests/vectors/
```

### neo-t8n

State transition tool (Ethereum-style) for deterministic execution-spec transitions.

```bash
# Run state transition
neo-t8n --input-alloc alloc.json \
        --input-txs txs.json \
        --input-env env.json \
        --output-result result.json
```

Input model:
- `alloc.json`: account map keyed by 20-byte hex address with optional `neoBalance`, `gasBalance`, `storage`, `nef`, `manifest`.
- `txs.json`: transaction array with `script` hex plus optional `signers`, `systemFee`, `networkFee`, `validUntilBlock`, `nonce`.
  - transaction array length is bounded by active profile `max_transactions_per_block` (`512` mainnet profile, `5000` testnet profile).
  - `script` must be valid hex and non-empty.
  - unsigned tx envelope size (header + signers + `attributes` varint count `0` + script var-size encoding) is capped at `102400` bytes.
  - `nonce` and `validUntilBlock` are validated as uint32 fields.
  - numeric tx fields also accept numeric strings (including `0x` prefixes) and are normalized for deterministic `txHash` materialization.
  - signer fields: `account`, `scopes`, `allowedContracts`, `allowedGroups`, optional `rules`.
  - signer array max length: 16.
  - `allowedContracts` / `allowedGroups` max length: 16 each.
  - `allowedContracts` requires `CUSTOM_CONTRACTS` scope; `allowedGroups` requires `CUSTOM_GROUPS` scope.
  - each `allowedGroups` entry must be a 33-byte compressed ECPoint key.
  - witness-rule fields: `action` (`0/1` or `Deny/Allow`) and `condition`.
  - witness-condition `type` accepts numeric tags or names (`Boolean`, `Not`, `And`, `Or`, `ScriptHash`, `Group`, `CalledByEntry`, `CalledByContract`, `CalledByGroup`).
- `env.json`: block context (`currentBlockNumber`, `timestamp`, `network`, `nonce`, `primaryIndex`).

`result.json` receipt model:
- `txHash`, `vmState`, `gasConsumed`, optional `exception`,
- `stack`: top-first projected VM stack items (`type` + `value`),
- `notifications`: projected runtime notifications with `contract`, `eventName`, and typed `state`.
- invalid tx input (bad/empty/oversized script, out-of-range `nonce`, negative/out-of-range fees, invalid `validUntilBlock`, signer count/list bound violations, duplicate signers, malformed signer scope/hash/group/rule fields, witness-rule depth/subitem/count limit violations, or malformed tx object/field types) is surfaced as a per-tx `FAULT` receipt.
- tx-list overflow (`len(txs)` exceeds `max_transactions_per_block`) produces per-tx `FAULT` receipts in default mode.
- processing continues across transaction lists even when one tx faults during validation/execution.
- `--strict` changes behavior to fail-fast and return non-zero exit on first tx validation/execution error.

`alloc-out.json`:
- post-state allocation in the same account-oriented schema as `alloc.json`.

Scope note:
- `neo-t8n` executes scripts with runtime context and state projection, but it is not a full mempool/consensus transaction validator.
- `result.receipts[*].txHash` is a deterministic `neo-t8n` receipt identifier, not a canonical network transaction hash.
