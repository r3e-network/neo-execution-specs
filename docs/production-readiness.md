# Production Readiness Checklist

This checklist defines the minimum bar for calling a release "production-ready" for `neo-execution-specs`.

## 1) Correctness and Regression Safety

- Run full suite:
  - `pytest`
- Ensure vector invariants stay green:
  - `cd tests/vectors && python validate.py`
  - `neo-coverage --checklist-template docs/verification/neo-v3.9.1-checklist-template.md --coverage-manifest tests/vectors/checklist_coverage.json --vectors-root tests/vectors/`

## 2) Cross-Client Compatibility

- Validate C# and NeoGo parity:
  - `neo-compat --vectors tests/vectors/ --csharp-rpc <csharp> --neogo-rpc <neogo>`
  - Optional: ignore documented external deltas with `--ignore-vectors-file <file>`
- Optional tri-client parity (with neo-rs endpoint):
  - `neo-multicompat --vectors tests/vectors/ --csharp-rpc <csharp> --neogo-rpc <neogo> --neo-rs-rpc <neo-rs>`
  - Optional: ignore documented external deltas with `--ignore-vectors-file <file>`

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
