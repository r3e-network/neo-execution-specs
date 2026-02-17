# Production Readiness Checklist

This checklist defines the minimum bar for calling a release "production-ready" for `neo-execution-specs`.
Canonical execution profile reference: `docs/execution-spec.md`.

## 1) Correctness and Regression Safety

- Run full suite:
  - `pytest`
- Ensure vector invariants stay green:
  - `cd tests/vectors && python validate.py`
  - `neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md --coverage-manifest tests/vectors/checklist_coverage.json --vectors-root tests/vectors/`
- Re-check native contract conformance locks:
  - `pytest -q tests/native/test_native_method_surface_v391.py`
  - Confirms v3.9.1 method surface + contract identity + locked method metadata across all native contracts.
- Re-check Policy governance/recovery invariants:
  - `pytest -q tests/native/test_policy.py`
  - Includes blocked-account vote clearing semantics across hardfork boundaries, one-year recover-fund delay, NEP-17 validation, and deployed-token transfer failure path.
- Re-check StdLib hardfork activation invariants:
  - `pytest -q tests/native/test_stdlib_fixes.py`
  - Includes Echidna/Faun activation checks for `base64Url*` and `hex*` methods, including native-engine unary dispatch path coverage.
- Re-check Ledger persistence/query invariants:
  - `pytest -q tests/native/test_ledger.py`
  - Includes persisted-block indexed transaction lookup (`getTransactionFromBlock`) and persisted transaction retrieval by hash.
- Re-check native dispatch marshalling invariants:
  - `pytest -q tests/smartcontract/test_native_handler_dispatch.py`
  - Includes stack-argument marshalling order, annotation-based `UInt160` conversion, snapshot-context injection, and StdLib `(value, context=None)` compatibility path.
- Re-check end-to-end native syscall dispatch:
  - `pytest -q tests/smartcontract/test_callnative_integration.py`
  - Includes `System.Contract.CallNative` method-offset dispatch with hardfork-aware active method maps, Neo v3.9.1 7-byte native stub semantics (`PUSH0 + SYSCALL + RET`), non-zero version rejection, context-aware handler invocation across signature classes, insufficient-call-flags rejection, hardfork activation boundaries for Echidna/Faun-gated methods, and VM stack return-type projection for native structured results (`Array`/`Map`/`ByteString` wrappers for `UInt160`/`UInt256`).
- Re-check native dynamic-call pathways:
  - `pytest -q tests/smartcontract/test_contract_call_native_integration.py`
  - Includes `System.Contract.Call` and `CALLT` dispatch to native contracts, native argument-order projection, caller-permission enforcement, and hardfork-gated native method activation checks.
- Re-check live native surface parity against Neo C# RPC:
  - `python3 scripts/check_native_surface_parity.py --rpc-url http://seed1.neo.org:10332`
  - Confirms IDs/hashes, full ABI method/event surfaces (including `safe` + offsets), standards, and `updatecounter` match `getnativecontracts`.

## 2) Cross-Client Compatibility

- Validate C# and NeoGo parity:
  - `neo-compat --vectors tests/vectors/ --csharp-rpc <csharp> --neogo-rpc <neogo>`
  - Optional: ignore documented external deltas with `--ignore-vectors-file <file>`
  - Current NeoGo 0.116 snapshot evidence: `docs/verification/neogo-0.116-validation-2026-02-16.md`
  - Current known NeoGo delta file: `docs/verification/neogo-0.116-known-deltas.txt`
  - Scheduled automation workflow: `.github/workflows/neogo-endpoint-matrix.yml`
- Optional public endpoint matrix automation:
    - `python3 scripts/neogo_endpoint_matrix.py --output-dir reports/compat-endpoint-matrix --prefix neogo-0.116-endpoint-matrix`
    - Default behavior also validates endpoint network magic and useragent tokens.
- Optional tri-client parity (with neo-rs endpoint):
  - `neo-multicompat --vectors tests/vectors/ --csharp-rpc <csharp> --neogo-rpc <neogo> --neo-rs-rpc <neo-rs>`
  - Optional: ignore documented external deltas with `--ignore-vectors-file <file>`

### Current compatibility snapshot (2026-02-16 UTC)

- C# 3.9.1 strict baseline: `405/405` on MainNet and TestNet.
- NeoGo 0.116 strict result: `400/405` on MainNet and TestNet, with stable 5-vector TRY/ENDTRY delta.
- Ignore-gated C#/NeoGo compatibility using `docs/verification/neogo-0.116-known-deltas.txt`: `Vector deltas: 0` on MainNet and TestNet.
- Public NeoGo endpoint matrix (`rpc1..rpc7` MainNet + `rpc.t5` TestNet): the same 5-vector delta reproduced on every endpoint.
- Tri-client caveat: local `neo-rs` endpoints were unavailable/incompatible in this environment (`0/405`, all `ERROR`), so tri-client parity is still pending valid `neo-rs` node setup.

## 3) Tooling and Packaging Integrity

- Lint:
  - `ruff check src tests scripts`
- Type regression:
  - `python scripts/check_mypy_regressions.py --baseline-file scripts/mypy-error-baseline.txt`
- Build tools:
  - `pip install build twine`
- Build artifacts:
  - `rm -rf dist build`
  - `python -m build --sdist --wheel`
  - `twine check dist/*`
- Smoke CLI entrypoints from built wheel:
  - `pip install --force-reinstall dist/*.whl`
  - `neo-diff --help`
  - `neo-compat --help`
  - `neo-multicompat --help`
  - `neo-coverage --help`
  - `neo-t8n --help`

## 4) Release Metadata Consistency

Before tagging:

- Run: `python scripts/check_release_metadata.py --tag vX.Y.Z`
- `pyproject.toml` `project.version` == `src/neo/__init__.py` `__version__`
- `CHANGELOG.md` contains `## [X.Y.Z] - YYYY-MM-DD`
- Git tag format is `vX.Y.Z`

The release workflow enforces these checks automatically.

## 5) Operational Hygiene

- Keep local validation artifacts out of VCS (`reports/`, `data/`, `.neo_go_ref/`, `.serena/`).
- Document behavior changes in `CHANGELOG.md`.
- Prefer backward-compatible defaults in CLI/tools.

## 6) Type Safety Gate

- Mypy baseline gate in CI is now strict (`scripts/mypy-error-baseline.txt` = `0`).
- Any new mypy error fails CI and must be fixed before release.
- Keep running the same full lint/test/vector gates; type safety complements, not replaces, runtime verification.
